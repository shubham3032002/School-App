from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Class,
    ClassEnrollment,
    Homework,
    HomeworkSubmission,
    Student,
    Teacher,
    TeacherClassAssignment,
    TimetableSlot,
)
from .permissions import IsTeacherOrAbove
from .serializers import (
    ClassEnrollmentReadSerializer,
    ClassEnrollmentWriteSerializer,
    ClassReadSerializer,
    ClassWriteSerializer,
    HomeworkReadSerializer,
    HomeworkSubmissionReadSerializer,
    HomeworkSubmissionWriteSerializer,
    HomeworkWriteSerializer,
    StudentReadSerializer,
    StudentWriteSerializer,
    TeacherClassAssignmentReadSerializer,
    TeacherClassAssignmentWriteSerializer,
    TeacherReadSerializer,
    TeacherWriteSerializer,
    TimetableSlotReadSerializer,
    TimetableSlotWriteSerializer,
)


ADMIN_ONLY     = ['admin']
ADMIN_HEAD     = ['admin', 'head']
PRINCIPAL_ADMIN = ['admin', 'principal']   # ✅ ADD
MANAGER_ABOVE  = ['manager', 'head', 'admin']

def has_role(user, roles):
    return bool(user and user.is_authenticated and user.role in roles)


def current_teacher(user):
    return getattr(user, 'teacher_profile', None)


def ensure_user_can_enroll_for_class(user, klass):
    if has_role(user, MANAGER_ABOVE):
        return

    teacher = current_teacher(user)
    if teacher is None:
        raise PermissionDenied('Teachers can enroll students only into assigned classes.')

    is_assigned = TeacherClassAssignment.objects.filter(
        teacher=teacher,
        klass=klass,
    ).exists()
    if not is_assigned:
        raise PermissionDenied('Teachers can enroll students only into assigned classes.')


def ensure_user_can_manage_homework(user, teacher):
    if has_role(user, ADMIN_HEAD):
        return
    if not has_role(user, ['staff']) or current_teacher(user) != teacher:
        raise PermissionDenied('Teachers can manage only their own homework.')


def get_student_or_error(request):
    student_id = request.data.get('student')
    if not student_id:
        return None, Response(
            {'student': 'Student id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return get_object_or_404(Student.objects.all(), pk=student_id), None


class RoleRestrictedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTeacherOrAbove]
    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return self.read_serializer_class
        return self.write_serializer_class

    def require_roles(self, roles):
        if not has_role(self.request.user, roles):
            raise PermissionDenied('You do not have permission to perform this action.')


class TeacherViewSet(RoleRestrictedViewSet):
    """Manage teacher profiles and teacher-specific timetable/homework views."""

    queryset = Teacher.objects.none()
    read_serializer_class = TeacherReadSerializer
    write_serializer_class = TeacherWriteSerializer

    def get_queryset(self):
        return Teacher.objects.select_related('user')

    def perform_create(self, serializer):
        self.require_roles(ADMIN_HEAD)
        serializer.save()

    def perform_update(self, serializer):
        self.require_roles(ADMIN_HEAD)
        serializer.save()

    def perform_destroy(self, instance):
        self.require_roles(ADMIN_HEAD)
        instance.delete()

    @action(detail=True, methods=['get'])
    def timetable(self, request, pk=None):
        """Return the full weekly timetable for a teacher."""
        teacher = get_object_or_404(self.get_queryset(), pk=pk)
        queryset = TimetableSlot.objects.select_related(
            'teacher__user',
            'klass',
        ).filter(teacher=teacher)
        serializer = TimetableSlotReadSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def homework(self, request, pk=None):
        """Return all homework assigned by a teacher."""
        teacher = get_object_or_404(self.get_queryset(), pk=pk)
        queryset = Homework.objects.select_related(
            'teacher__user',
            'klass',
        ).filter(teacher=teacher)
        serializer = HomeworkReadSerializer(queryset, many=True)
        return Response(serializer.data)


class ClassViewSet(RoleRestrictedViewSet):
    """Manage classes, active rosters, and student enrollment workflows."""

    queryset = Class.objects.none()
    read_serializer_class = ClassReadSerializer
    write_serializer_class = ClassWriteSerializer

    def get_queryset(self):
        return Class.objects.select_related('homeroom_teacher__user').prefetch_related(
            'enrollments__student',
            'teacher_assignments__teacher__user',
        )

    def perform_create(self, serializer):
        # ✅ Only admin can create a class
        self.require_roles(ADMIN_ONLY)
        serializer.save()

    def perform_update(self, serializer):
        # ✅ Admin or Principal can update (assign class teacher)
        self.require_roles(PRINCIPAL_ADMIN)
        serializer.save()

    def perform_destroy(self, instance):
        self.require_roles(ADMIN_ONLY)
        instance.delete()

    def ensure_can_enroll_for_class(self, klass):
        ensure_user_can_enroll_for_class(self.request.user, klass)

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Return active students enrolled in a class."""
        klass = get_object_or_404(self.get_queryset(), pk=pk)
        queryset = Student.objects.filter(
            enrollments__klass=klass,
            enrollments__status=ClassEnrollment.Status.ACTIVE,
        )
        serializer = StudentReadSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Enroll a student into this class as their active class."""
        klass = get_object_or_404(self.get_queryset(), pk=pk)
        self.ensure_can_enroll_for_class(klass)
        student, error_response = get_student_or_error(request)
        if error_response:
            return error_response

        if ClassEnrollment.objects.filter(
            student=student,
            status=ClassEnrollment.Status.ACTIVE,
        ).exists():
            return Response(
                {'student': 'Student already has an active class enrollment.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            enrollment = ClassEnrollment.objects.create(
                klass=klass,
                student=student,
                enrolled_by=current_teacher(request.user),
                enrollment_date=request.data.get('enrollment_date') or timezone.localdate(),
                status=ClassEnrollment.Status.ACTIVE,
            )

        serializer = ClassEnrollmentReadSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def unenroll(self, request, pk=None):
        """Mark a student's active enrollment in this class as dropped."""
        klass = get_object_or_404(self.get_queryset(), pk=pk)
        self.ensure_can_enroll_for_class(klass)
        student, error_response = get_student_or_error(request)
        if error_response:
            return error_response
        enrollment = get_object_or_404(
            ClassEnrollment.objects.select_related('klass', 'student', 'enrolled_by__user'),
            klass=klass,
            student=student,
            status=ClassEnrollment.Status.ACTIVE,
        )

        with transaction.atomic():
            enrollment.status = ClassEnrollment.Status.DROPPED
            enrollment.save(update_fields=['status'])

        serializer = ClassEnrollmentReadSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'], url_path='assign-class-teacher')
    def assign_class_teacher(self, request, pk=None):
        """
        PATCH /api/classes/<id>/assign-class-teacher/
        Body: { "class_teacher": 3, "secondary_class_teacher": 5 }
        Only principal or admin can call this.
        """
        if not has_role(request.user, ['admin', 'principal']):
            raise PermissionDenied('Only admin or principal can assign class teachers.')

        klass = get_object_or_404(self.get_queryset(), pk=pk)

        ct_id  = request.data.get('class_teacher')
        sct_id = request.data.get('secondary_class_teacher')

        if ct_id is not None:
            klass.class_teacher = get_object_or_404(Teacher, pk=ct_id)
        if sct_id is not None:
            klass.secondary_class_teacher = get_object_or_404(Teacher, pk=sct_id)

        klass.save()
        return Response(ClassReadSerializer(klass).data)



class TeacherClassAssignmentViewSet(RoleRestrictedViewSet):
    """Manage teacher-to-class subject assignments. Only principal or admin can assign."""

    queryset = TeacherClassAssignment.objects.none()
    read_serializer_class = TeacherClassAssignmentReadSerializer
    write_serializer_class = TeacherClassAssignmentWriteSerializer

    def get_queryset(self):
        return TeacherClassAssignment.objects.select_related('teacher__user', 'klass')

    def perform_create(self, serializer):
        self.require_roles(PRINCIPAL_ADMIN)
        serializer.save()

    def perform_update(self, serializer):
        self.require_roles(PRINCIPAL_ADMIN)
        serializer.save()

    def perform_destroy(self, instance):
        self.require_roles(PRINCIPAL_ADMIN)
        instance.delete()


class TimetableSlotViewSet(RoleRestrictedViewSet):
    """Manage timetable slots for teachers and classes."""

    queryset = TimetableSlot.objects.none()
    read_serializer_class = TimetableSlotReadSerializer
    write_serializer_class = TimetableSlotWriteSerializer

    def get_queryset(self):
        return TimetableSlot.objects.select_related('teacher__user', 'klass')

    def ensure_can_manage_slot(self, teacher):
        if has_role(self.request.user, ADMIN_HEAD):
            return
        if (
            not has_role(self.request.user, ['staff'])
            or current_teacher(self.request.user) != teacher
        ):
            raise PermissionDenied('Teachers can manage only their own timetable.')

    def perform_create(self, serializer):
        self.ensure_can_manage_slot(serializer.validated_data['teacher'])
        serializer.save()

    def perform_update(self, serializer):
        teacher = serializer.validated_data.get('teacher', serializer.instance.teacher)
        self.ensure_can_manage_slot(teacher)
        serializer.save()

    def perform_destroy(self, instance):
        self.ensure_can_manage_slot(instance.teacher)
        instance.delete()


class StudentViewSet(RoleRestrictedViewSet):
    """Manage students and expose student enrollment/homework/submission views."""

    queryset = Student.objects.none()
    read_serializer_class = StudentReadSerializer
    write_serializer_class = StudentWriteSerializer

    def get_queryset(self):
        return Student.objects.prefetch_related(
            'enrollments__klass',
            'homework_submissions__homework',
        )

    def perform_create(self, serializer):
        self.require_roles(ADMIN_HEAD)
        serializer.save()

    def perform_update(self, serializer):
        self.require_roles(ADMIN_HEAD)
        serializer.save()

    def perform_destroy(self, instance):
        self.require_roles(ADMIN_HEAD)
        instance.delete()

    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Return enrollment history for a student."""
        student = get_object_or_404(self.get_queryset(), pk=pk)
        queryset = ClassEnrollment.objects.select_related(
            'klass',
            'student',
            'enrolled_by__user',
        ).filter(student=student)
        serializer = ClassEnrollmentReadSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def homework(self, request, pk=None):
        """Return all homework assigned to the student's active class."""
        student = get_object_or_404(self.get_queryset(), pk=pk)
        active_enrollment = ClassEnrollment.objects.filter(
            student=student,
            status=ClassEnrollment.Status.ACTIVE,
        ).first()
        if active_enrollment is None:
            return Response([])

        queryset = Homework.objects.select_related('teacher__user', 'klass').filter(
            klass=active_enrollment.klass,
        )
        serializer = HomeworkReadSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Return all homework submissions by a student."""
        student = get_object_or_404(self.get_queryset(), pk=pk)
        queryset = HomeworkSubmission.objects.select_related(
            'homework__klass',
            'student',
        ).filter(student=student)
        serializer = HomeworkSubmissionReadSerializer(queryset, many=True)
        return Response(serializer.data)


class ClassEnrollmentViewSet(RoleRestrictedViewSet):
    """Manage class enrollment records."""

    queryset = ClassEnrollment.objects.none()
    read_serializer_class = ClassEnrollmentReadSerializer
    write_serializer_class = ClassEnrollmentWriteSerializer

    def get_queryset(self):
        return ClassEnrollment.objects.select_related('klass', 'student', 'enrolled_by__user')

    def perform_create(self, serializer):
        klass = serializer.validated_data['klass']
        ensure_user_can_enroll_for_class(self.request.user, klass)
        serializer.save(enrolled_by=current_teacher(self.request.user))

    def perform_update(self, serializer):
        klass = serializer.validated_data.get('klass', serializer.instance.klass)
        ensure_user_can_enroll_for_class(self.request.user, klass)
        serializer.save()

    def perform_destroy(self, instance):
        ensure_user_can_enroll_for_class(self.request.user, instance.klass)
        instance.delete()


class HomeworkViewSet(RoleRestrictedViewSet):
    """Manage homework and homework submission workflows."""

    queryset = Homework.objects.none()
    read_serializer_class = HomeworkReadSerializer
    write_serializer_class = HomeworkWriteSerializer

    def get_queryset(self):
        return Homework.objects.select_related('teacher__user', 'klass').prefetch_related(
            'submissions__student',
        )

    def ensure_can_manage_homework(self, teacher):
        ensure_user_can_manage_homework(self.request.user, teacher)

    def perform_create(self, serializer):
        self.ensure_can_manage_homework(serializer.validated_data['teacher'])
        serializer.save()

    def perform_update(self, serializer):
        teacher = serializer.validated_data.get('teacher', serializer.instance.teacher)
        self.ensure_can_manage_homework(teacher)
        serializer.save()

    def perform_destroy(self, instance):
        self.ensure_can_manage_homework(instance.teacher)
        instance.delete()

    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Return all submissions for this homework."""
        homework = get_object_or_404(self.get_queryset(), pk=pk)
        queryset = HomeworkSubmission.objects.select_related(
            'homework__klass',
            'student',
        ).filter(homework=homework)
        serializer = HomeworkSubmissionReadSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Create or update a student's submission for this homework."""
        homework = get_object_or_404(self.get_queryset(), pk=pk)
        student, error_response = get_student_or_error(request)
        if error_response:
            return error_response
        is_enrolled = ClassEnrollment.objects.filter(
            klass=homework.klass,
            student=student,
            status=ClassEnrollment.Status.ACTIVE,
        ).exists()
        if not is_enrolled:
            return Response(
                {'student': 'Student is not actively enrolled in this homework class.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submitted_at = timezone.now()
        submission_status = HomeworkSubmission.SubmissionStatus.SUBMITTED
        if submitted_at.date() > homework.due_date:
            submission_status = HomeworkSubmission.SubmissionStatus.LATE

        with transaction.atomic():
            submission, _ = HomeworkSubmission.objects.update_or_create(
                homework=homework,
                student=student,
                defaults={
                    'submission_notes': request.data.get('submission_notes', ''),
                    'submission_status': submission_status,
                    'submitted_at': submitted_at,
                },
            )

        serializer = HomeworkSubmissionReadSerializer(submission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def grade_submission(self, request, homework_pk=None, submission_id=None):
        """Grade a specific submission for this homework."""
        homework = get_object_or_404(self.get_queryset(), pk=homework_pk)
        self.ensure_can_manage_homework(homework.teacher)
        submission = get_object_or_404(
            HomeworkSubmission.objects.select_related('homework__klass', 'student'),
            pk=submission_id,
            homework=homework,
        )
        serializer = HomeworkSubmissionWriteSerializer(
            submission,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(HomeworkSubmissionReadSerializer(submission).data)


class HomeworkSubmissionViewSet(RoleRestrictedViewSet):
    """Manage homework submission records."""

    queryset = HomeworkSubmission.objects.none()
    read_serializer_class = HomeworkSubmissionReadSerializer
    write_serializer_class = HomeworkSubmissionWriteSerializer

    def get_queryset(self):
        return HomeworkSubmission.objects.select_related(
            'homework__teacher__user',
            'homework__klass',
            'student',
        )

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        homework = serializer.validated_data.get('homework', serializer.instance.homework)
        if 'grade' in serializer.validated_data:
            ensure_user_can_manage_homework(self.request.user, homework.teacher)
        serializer.save()

    def perform_destroy(self, instance):
        ensure_user_can_manage_homework(self.request.user, instance.homework.teacher)
        instance.delete()
