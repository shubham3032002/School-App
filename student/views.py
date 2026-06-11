from django.shortcuts import render

from rest_framework import generics ,status , filters
from rest_framework.permissions import IsAuthenticated
from  rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

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
# Student CRUD
# ─────────────────────────────────────────────

class StudentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/student/students/ - List all students
    post /api/student/students/ - Create a new student
    """


    permission_classes = [IsAuthenticated, IsAdminOrHead]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'admission_number', 'roll_number']
    ordering_fields = ['first_name', 'last_name', 'admission_number', 'created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentWriteSerializer
        return StudentReadSerializer
    
    def get_queryset(self):
        queryset =Student.objects.select_related('class_id')

        class_id = self.request.query_params.get('class_id')
        section  = self.request.query_params.get('section')

        if class_id:
            queryset = queryset.filter(class_id=class_id)
        if section:
            queryset = queryset.filter(section=section)

        return queryset



class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
     """
    GET    /api/student/students/<id>/  — get student
    PUT    /api/student/students/<id>/  — full update
    PATCH  /api/student/students/<id>/  — partial update
    DELETE /api/student/students/<id>/  — delete student
    Admin / head only.
    """
     
     permission_classes = [IsAuthenticated, IsAdminOrHead]

     queryset = Student.objects.select_related('class_id')


     def get_serializer_class(self):
         if self.request.method in ['PUT', 'PATCH']:
             return StudentWriteSerializer
         return StudentReadSerializer
     


class AttendanceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/student/attendance/  — list attendance (teacher sees own class only)
    POST /api/student/attendance/  — mark single attendance (homeroom teacher only)
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

        # Optional filters
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

        # Only homeroom teacher of this class can mark attendance
        if klass.homeroom_teacher != teacher:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only the homeroom teacher can mark attendance for this class.')

        serializer.save(teacher=teacher)

class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/student/attendance/<id>/  — get single record
    PUT   /api/student/attendance/<id>/  — update record
    PATCH /api/student/attendance/<id>/  — partial update
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

        # Only homeroom teacher allowed
        if klass.homeroom_teacher != teacher:
            return Response(
                {'detail': 'Only the homeroom teacher can mark attendance for this class.'},
                status=status.HTTP_403_FORBIDDEN
            )

        created = 0
        updated = 0

        for record in data['records']:
            student = get_object_or_404(Student, id=record['student'])

            # Create new or update existing attendance record
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
    Useful for daily attendance dashboard.
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