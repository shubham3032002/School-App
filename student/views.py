from django.shortcuts import render

from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.exceptions import AuthenticationFailed

from teacher.models import Class
from .models import Student, AttendanceRecord
from .serializers import (
    StudentWriteSerializer,
    StudentReadSerializer,
    AttendanceWriteSerializer,
    AttendanceReadSerializer,
    BulkAttendanceSerializer,
)
from .permissions import IsAdminOrHead, IsTeacher, IsHomeroomTeacher


# ─────────────────────────────────────────────
# Helper — decode student JWT
# ─────────────────────────────────────────────

def get_student_from_token(request):
    """
    Decode the Bearer token and return the Student instance.
    Raises AuthenticationFailed if token is missing, invalid, or not a student token.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationFailed('Bearer token required.')

    raw_token = auth_header.split(' ')[1]

    try:
        token = AccessToken(raw_token)
    except Exception:
        raise AuthenticationFailed('Token is invalid or expired.')

    if token.get('type') != 'student':
        raise AuthenticationFailed('Not a student token.')

    student_id = token.get('student_id')
    try:
        return Student.objects.select_related('class_id').get(id=student_id)
    except Student.DoesNotExist:
        raise AuthenticationFailed('Student not found.')


# ─────────────────────────────────────────────
# Student CRUD
# ─────────────────────────────────────────────

class StudentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/student/          - List all students
    POST /api/student/          - Create a new student
    Admin / head only.
    """
    permission_classes = [IsAuthenticated, IsAdminOrHead]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['first_name', 'last_name', 'admission_number', 'roll_number']
    ordering_fields    = ['first_name', 'last_name', 'admission_number', 'created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentWriteSerializer
        return StudentReadSerializer

    def get_queryset(self):
        queryset = Student.objects.select_related('class_id')

        class_id = self.request.query_params.get('class_id')
        section  = self.request.query_params.get('section')

        if class_id:
            queryset = queryset.filter(class_id=class_id)
        if section:
            queryset = queryset.filter(section=section)

        return queryset


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/student/<id>/  - get student
    PUT    /api/student/<id>/  - full update
    PATCH  /api/student/<id>/  - partial update
    DELETE /api/student/<id>/  - delete student
    Admin / head only.
    """
    permission_classes = [IsAuthenticated, IsAdminOrHead]
    queryset           = Student.objects.select_related('class_id')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StudentWriteSerializer
        return StudentReadSerializer


# ─────────────────────────────────────────────
# Student Auth
# ─────────────────────────────────────────────

class StudentLoginView(APIView):
    """
    POST /api/student/login/
    {
        "admission_number": "ADM001",
        "password": "password@123"
    }
    """
    permission_classes     = []   # public endpoint
    authentication_classes = []   # no auth needed

    def post(self, request):
        admission_number = request.data.get('admission_number')
        password         = request.data.get('password')

        if not admission_number or not password:
            return Response(
                {'detail': 'admission_number and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(admission_number=admission_number)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, student.password):
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Issue JWT token with student info embedded
        refresh = RefreshToken()
        refresh['student_id']       = student.id
        refresh['admission_number'] = student.admission_number
        refresh['type']             = 'student'

        return Response({
            'refresh':          str(refresh),
            'access':           str(refresh.access_token),
            'student_id':       student.id,
            'admission_number': student.admission_number,
            'full_name':        f"{student.first_name} {student.last_name}",
        }, status=status.HTTP_200_OK)


class StudentProfileView(APIView):
    """
    GET /api/student/profile/
    Returns the profile of the logged-in student only.
    Requires the student's own Bearer token from login.
    """
    permission_classes     = []   # we manually validate the student token
    authentication_classes = []

    def get(self, request):
        student    = get_student_from_token(request)
        serializer = StudentReadSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentChangePasswordView(APIView):
    """
    POST /api/student/change-password/
    {
        "admission_number": "ADM001",
        "old_password": "password@123",
        "new_password": "newpass123"
    }
    """
    permission_classes     = []   # student has no Django user so no IsAuthenticated
    authentication_classes = []

    def post(self, request):
        admission_number = request.data.get('admission_number')
        old_password     = request.data.get('old_password')
        new_password     = request.data.get('new_password')

        if not all([admission_number, old_password, new_password]):
            return Response(
                {'detail': 'admission_number, old_password and new_password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(admission_number=admission_number)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(old_password, student.password):
            return Response(
                {'detail': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if old_password == new_password:
            return Response(
                {'detail': 'New password must be different from old password.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        student.password = make_password(new_password)
        student.save()

        return Response({'detail': 'Password changed successfully.'})


# ─────────────────────────────────────────────
# Attendance
# ─────────────────────────────────────────────

class AttendanceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/student/attendance/  - list attendance (teacher sees own class only)
    POST /api/student/attendance/  - mark single attendance (homeroom teacher only)
    Filters: ?klass=1  ?date=2026-06-11  ?student=5  ?status=Absent
    """
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AttendanceWriteSerializer
        return AttendanceReadSerializer

    def get_queryset(self):
        qs      = AttendanceRecord.objects.select_related('student', 'klass', 'teacher__user')
        teacher = self.request.user.teacher_profile

        # Teachers only see their own homeroom class attendance
        qs = qs.filter(klass__homeroom_teacher=teacher)

        klass   = self.request.query_params.get('klass')
        date    = self.request.query_params.get('date')
        student = self.request.query_params.get('student')
        status  = self.request.query_params.get('status')

        if klass:
            qs = qs.filter(klass_id=klass)
        if date:
            qs = qs.filter(attendance_date=date)
        if student:
            qs = qs.filter(student_id=student)
        if status:
            qs = qs.filter(status=status)

        return qs

    def perform_create(self, serializer):
        teacher = self.request.user.teacher_profile
        klass   = serializer.validated_data['klass']

        if klass.homeroom_teacher != teacher:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only the homeroom teacher can mark attendance for this class.')

        serializer.save(teacher=teacher)


class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/student/attendance/<id>/  - get single record
    PUT   /api/student/attendance/<id>/  - update record
    PATCH /api/student/attendance/<id>/  - partial update
    No DELETE — attendance records are permanent.
    Only homeroom teacher of that class allowed.
    """
    permission_classes = [IsAuthenticated, IsHomeroomTeacher]
    queryset           = AttendanceRecord.objects.select_related('student', 'klass', 'teacher__user')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AttendanceWriteSerializer
        return AttendanceReadSerializer


# ─────────────────────────────────────────────
# Attendance — Bulk Mark for Entire Class
# ─────────────────────────────────────────────

class BulkAttendanceView(APIView):
    """
    POST /api/student/attendance/bulk/
    Mark attendance for ALL students in a class in one request.
    If a record already exists for that student+date it gets updated.
    Only homeroom teacher of the class allowed.
    """
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data            = serializer.validated_data
        klass           = get_object_or_404(Class, id=data['klass'])
        attendance_date = data['attendance_date']
        teacher         = request.user.teacher_profile

        if klass.homeroom_teacher != teacher:
            return Response(
                {'detail': 'Only the homeroom teacher can mark attendance for this class.'},
                status=status.HTTP_403_FORBIDDEN
            )

        created = 0
        updated = 0

        for record in data['records']:
            student = get_object_or_404(Student, id=record['student'])

            obj, is_new = AttendanceRecord.objects.update_or_create(
                student=student,
                attendance_date=attendance_date,
                defaults={
                    'klass':   klass,
                    'teacher': teacher,
                    'status':  record['status'],
                    'remarks': record.get('remarks', ''),
                }
            )
            if is_new:
                created += 1
            else:
                updated += 1

        return Response({
            'detail': f'{created} created, {updated} updated.',
            'date':   str(attendance_date),
            'class':  klass.name,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Helper — Students in a Class
# ─────────────────────────────────────────────

class ClassStudentsView(APIView):
    """
    GET /api/student/classes/<klass_id>/students/
    Returns all students in a class.
    Used by teacher to load the attendance sheet before marking.
    """
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, klass_id):
        klass    = get_object_or_404(Class, id=klass_id)
        students = Student.objects.filter(
            class_id=klass
        ).order_by('roll_number', 'first_name')

        data = [
            {
                'id':               s.id,
                'full_name':        f"{s.first_name} {s.last_name}",
                'admission_number': s.admission_number,
                'roll_number':      s.roll_number,
                'section':          s.section,
                'gender':           s.gender,
            }
            for s in students
        ]

        return Response({
            'class_id':   klass.id,
            'class_name': klass.name,
            'total':      len(data),
            'students':   data,
        })


# ─────────────────────────────────────────────
# Attendance Summary Report
# ─────────────────────────────────────────────

class AttendanceSummaryView(APIView):
    """
    GET /api/student/attendance/summary/?klass=1&date=2026-06-11
    Returns count of each status for a class on a given date.
    """
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        klass_id = request.query_params.get('klass')
        date     = request.query_params.get('date')

        if not klass_id or not date:
            return Response(
                {'detail': 'Both klass and date query params are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        klass   = get_object_or_404(Class, id=klass_id)
        records = AttendanceRecord.objects.filter(klass=klass, attendance_date=date)

        return Response({
            'class':    klass.name,
            'date':     date,
            'total':    records.count(),
            'Present':  records.filter(status='Present').count(),
            'Absent':   records.filter(status='Absent').count(),
            'Late':     records.filter(status='Late').count(),
            'Half Day': records.filter(status='Half Day').count(),
            'Leave':    records.filter(status='Leave').count(),
        })