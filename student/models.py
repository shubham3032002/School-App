from django.db import models
from teacher.models import Class, Teacher


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE   = 'Male',   'Male'
        FEMALE = 'Female', 'Female'
 

    id               = models.AutoField(primary_key=True)
    admission_number = models.CharField(max_length=20, unique=True)
    first_name       = models.CharField(max_length=100)
    last_name        = models.CharField(max_length=100)
    gender           = models.CharField(max_length=10, choices=Gender.choices)
    date_of_birth    = models.DateField()
    class_id         = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    section          = models.CharField(max_length=10)
    roll_number      = models.CharField(max_length=10)
    address          = models.TextField(blank=True, null=True)
    phone            = models.CharField(max_length=15, blank=True, null=True)
    email            = models.EmailField(max_length=100, unique=True, blank=True, null=True)
    guardian_name    = models.CharField(max_length=100, blank=True, null=True)
    guardian_phone   = models.CharField(max_length=15, blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128)

    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name = 'student'
        verbose_name_plural = 'students'
        constraints = [
            models.CheckConstraint(
                check=models.Q(gender__in=['Male', 'Female', 'Other']),
                name='valid_student_gender',
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT  = 'Present',  'Present'
        ABSENT   = 'Absent',   'Absent'
        LATE     = 'Late',     'Late'
        HALF_DAY = 'Half Day', 'Half Day'
        LEAVE    = 'Leave',    'Leave'
    id              = models.AutoField(primary_key=True)    
    student         = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    klass           = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='student_attendance')
    teacher         = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='marked_attendance')
    attendance_date = models.DateField()
    status          = models.CharField(max_length=10, choices=Status.choices)
    remarks         = models.TextField(blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attendance_date', 'student__first_name']
        unique_together = ('student', 'attendance_date')
        verbose_name = 'attendance record'
        verbose_name_plural = 'attendance records'

    def __str__(self):
        return f"{self.student} - {self.attendance_date} - {self.status}"