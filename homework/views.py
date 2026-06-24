from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from teacher.models import Teacher
from student.models import Student
from .models import Homework, HomeworkSubmission
from .permissions import IsAssignedTeacher
from .serializers import (
    HomeworkReadSerializer,
    HomeworkWriteSerializer,
    HomeworkSubmissionReadSerializer,
    HomeworkSubmissionWriteSerializer,
)

ALLOWED_IMAGE_TYPES  = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


# ─────────────────────────────────────────────
# Helper — decode student JWT
# ─────────────────────────────────────────────

def get_student_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationFailed('Bearer token required.')
    try:
        token = AccessToken(auth_header.split(' ')[1])
    except Exception:
        raise AuthenticationFailed('Token is invalid or expired.')
    if token.get('type') != 'student':
        raise AuthenticationFailed('Not a student token.')
    try:
        return Student.objects.select_related('class_id').get(id=token.get('student_id'))
    except Student.DoesNotExist:
        raise AuthenticationFailed('Student not found.')


# ─────────────────────────────────────────────
# Teacher — Homework CRUD
# ─────────────────────────────────────────────

class HomeworkListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/homework/   — teacher sees only their own homework
    POST /api/homework/   — teacher creates homework for their class
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return HomeworkWriteSerializer if self.request.method == 'POST' else HomeworkReadSerializer

    def get_queryset(self):
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)

        if user.role in ['admin', 'principal']:
            qs = Homework.objects.select_related('teacher__user', 'klass').all()
        elif teacher:
            qs = Homework.objects.select_related('teacher__user', 'klass').filter(teacher=teacher)
        else:
            return Homework.objects.none()

        klass_id  = self.request.query_params.get('klass')
        subject   = self.request.query_params.get('subject')
        hw_status = self.request.query_params.get('status')
        if klass_id:  qs = qs.filter(klass_id=klass_id)
        if subject:   qs = qs.filter(subject__icontains=subject)
        if hw_status: qs = qs.filter(status=hw_status)
        return qs

    def perform_create(self, serializer):
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)

        if user.role in ['admin', 'principal']:
            serializer.save()
            return

        if teacher is None:
            raise PermissionDenied('Only teachers can create homework.')

        klass = serializer.validated_data.get('klass')

        from teacher.models import TeacherClassAssignment
        is_assigned = TeacherClassAssignment.objects.filter(
            teacher=teacher, klass=klass
        ).exists()
        if not is_assigned:
            raise PermissionDenied('You can only assign homework to classes you teach.')

        if serializer.validated_data.get('teacher') != teacher:
            raise PermissionDenied('You can only create homework under your own name.')

        serializer.save()


class HomeworkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/homework/<id>/
    PATCH  /api/homework/<id>/
    DELETE /api/homework/<id>/
    """
    permission_classes = [IsAuthenticated, IsAssignedTeacher]

    def get_serializer_class(self):
        return HomeworkWriteSerializer if self.request.method in ['PUT', 'PATCH'] else HomeworkReadSerializer

    def get_queryset(self):
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)
        if user.role in ['admin', 'principal']:
            return Homework.objects.select_related('teacher__user', 'klass').all()
        if teacher:
            return Homework.objects.select_related('teacher__user', 'klass').filter(teacher=teacher)
        return Homework.objects.none()


# ─────────────────────────────────────────────
# Teacher — view & grade submissions
# ─────────────────────────────────────────────

class HomeworkSubmissionsView(generics.ListAPIView):
    """
    GET /api/homework/<homework_id>/submissions/
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = HomeworkSubmissionReadSerializer

    def get_queryset(self):
        homework_id = self.kwargs['homework_id']
        user        = self.request.user
        teacher     = getattr(user, 'teacher_profile', None)

        homework = get_object_or_404(Homework, pk=homework_id)

        if user.role not in ['admin', 'principal']:
            if teacher is None or homework.teacher != teacher:
                raise PermissionDenied('You can only view submissions for your own homework.')

        return HomeworkSubmission.objects.select_related(
            'student', 'homework__klass'
        ).filter(homework=homework)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class GradeSubmissionView(generics.UpdateAPIView):
    """
    PATCH /api/homework/submissions/<id>/grade/
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = HomeworkSubmissionWriteSerializer

    def get_queryset(self):
        return HomeworkSubmission.objects.select_related('homework__teacher', 'student')

    def perform_update(self, serializer):
        submission = self.get_object()
        user       = self.request.user
        teacher    = getattr(user, 'teacher_profile', None)

        if user.role not in ['admin', 'principal']:
            if teacher is None or submission.homework.teacher != teacher:
                raise PermissionDenied('You can only grade submissions for your own homework.')

        serializer.save()


# ─────────────────────────────────────────────
# Student — view homework for their class
# ─────────────────────────────────────────────

class StudentHomeworkListView(APIView):
    """
    GET /api/homework/student/my-homework/
    """
    permission_classes     = []
    authentication_classes = []

    def get(self, request):
        student = get_student_from_token(request)

        if student.class_id is None:
            return Response(
                {'detail': 'You are not assigned to any class.'},
                status=status.HTTP_200_OK,
            )

        homework = Homework.objects.select_related('teacher__user', 'klass').filter(
            klass=student.class_id,
            status=Homework.Status.PUBLISHED,
        ).order_by('-assigned_date')

        serializer = HomeworkReadSerializer(homework, many=True, context={'request': request})
        return Response({
            'class':    student.class_id.name,
            'total':    homework.count(),
            'homework': serializer.data,
        })


class StudentSubmitHomeworkView(APIView):
    """
    POST /api/homework/<homework_id>/submit/
    Content-Type: multipart/form-data
    Fields:
        submission_notes  (text, optional)
        submission_image  (image file, optional — JPEG/PNG/WEBP/GIF, max 5 MB)
    """
    permission_classes     = []
    authentication_classes = []

    def post(self, request, homework_id):
        student  = get_student_from_token(request)
        homework = get_object_or_404(Homework, pk=homework_id, status=Homework.Status.PUBLISHED)

        if student.class_id != homework.klass:
            return Response(
                {'detail': 'This homework is not assigned to your class.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate image before touching the DB
        image_file = request.FILES.get('submission_image')
        if image_file:
            if image_file.content_type not in ALLOWED_IMAGE_TYPES:
                return Response(
                    {'submission_image': 'Only JPEG, PNG, WEBP, or GIF images are allowed.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if image_file.size > MAX_IMAGE_SIZE_BYTES:
                return Response(
                    {'submission_image': 'Image must be smaller than 5 MB.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        submitted_at      = timezone.now()
        submission_status = (
            HomeworkSubmission.SubmissionStatus.LATE
            if submitted_at.date() > homework.due_date
            else HomeworkSubmission.SubmissionStatus.SUBMITTED
        )

        # Delete old image from disk if student is re-submitting with a new image
        existing = HomeworkSubmission.objects.filter(
            homework=homework, student=student
        ).first()
        if image_file and existing and existing.submission_image:
            existing.submission_image.delete(save=False)

        defaults = {
            'submission_notes':  request.data.get('submission_notes', ''),
            'submission_status': submission_status,
            'submitted_at':      submitted_at,
        }
        if image_file:
            defaults['submission_image'] = image_file

        submission, created = HomeworkSubmission.objects.update_or_create(
            homework=homework,
            student=student,
            defaults=defaults,
        )

        serializer = HomeworkSubmissionReadSerializer(submission, context={'request': request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class StudentMySubmissionsView(APIView):
    """
    GET /api/homework/student/my-submissions/
    """
    permission_classes     = []
    authentication_classes = []

    def get(self, request):
        student = get_student_from_token(request)
        submissions = HomeworkSubmission.objects.select_related(
            'homework__klass', 'homework__teacher__user'
        ).filter(student=student).order_by('-homework__due_date')

        serializer = HomeworkSubmissionReadSerializer(
            submissions, many=True, context={'request': request}
        )
        return Response({'total': submissions.count(), 'submissions': serializer.data})