from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
    )
    phone = models.CharField(max_length=20, blank=True)
    subject_specialization = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__fullname']
        verbose_name = 'teacher'
        verbose_name_plural = 'teachers'

    def __str__(self):
        return self.user.fullname


class Class(models.Model):
    name             = models.CharField(max_length=80)
    grade_level      = models.CharField(max_length=20)
    section          = models.CharField(max_length=10, blank=True)
    academic_year    = models.PositiveSmallIntegerField()

    homeroom_teacher = models.ForeignKey(          # rename this → class_teacher
        Teacher,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='homeroom_classes',
    )

    # ✅ ADD THIS
    class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='class_teacher_classes',
        help_text='Primary class teacher who owns this class.',
    )

    # ✅ ADD THIS
    secondary_class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='secondary_class_teacher_classes',
        help_text='Secondary/co-class teacher.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
class TeacherClassAssignment(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='class_assignments',
    )
    klass = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='teacher_assignments',
    )
    subject = models.CharField(max_length=80)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['klass__academic_year', 'klass__grade_level', 'subject']
        verbose_name = 'teacher class assignment'
        verbose_name_plural = 'teacher class assignments'
        unique_together = ('teacher', 'klass', 'subject')

    def __str__(self):
        return f'{self.teacher} teaches {self.subject} for {self.klass}'


class TimetableSlot(models.Model):
    class DayOfWeek(models.TextChoices):
        MONDAY = 'Monday', 'Monday'
        TUESDAY = 'Tuesday', 'Tuesday'
        WEDNESDAY = 'Wednesday', 'Wednesday'
        THURSDAY = 'Thursday', 'Thursday'
        FRIDAY = 'Friday', 'Friday'
        SATURDAY = 'Saturday', 'Saturday'
        SUNDAY = 'Sunday', 'Sunday'

    class SlotType(models.TextChoices):
        LECTURE = 'lecture', 'Lecture'
        LAB = 'lab', 'Lab'
        SPORTS = 'sports', 'Sports'
        FREE = 'free', 'Free'

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
    )
    klass = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
    )
    subject = models.CharField(max_length=80)
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20, blank=True)
    slot_type = models.CharField(
        max_length=10,
        choices=SlotType.choices,
        default=SlotType.LECTURE,
    )

    class Meta:
        ordering = ['day_of_week', 'start_time', 'klass__name']
        verbose_name = 'timetable slot'
        verbose_name_plural = 'timetable slots'
        unique_together = (
            ('teacher', 'day_of_week', 'start_time'),
            ('klass', 'day_of_week', 'start_time'),
        )
        constraints = [
            models.CheckConstraint(
                check=Q(end_time__gt=models.F('start_time')),
                name='timetable_end_time_after_start_time',
            ),
        ]

    def __str__(self):
        return f'{self.teacher} - {self.subject} - {self.day_of_week} {self.start_time}'


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    full_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    parent_contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'student'
        verbose_name_plural = 'students'

    def __str__(self):
        return f'{self.full_name} ({self.roll_number})'


class ClassEnrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        TRANSFERRED = 'transferred', 'Transferred'
        DROPPED = 'dropped', 'Dropped'

    klass = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    enrolled_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrollments_created',
    )
    enrollment_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ['-enrollment_date', 'student__full_name']
        verbose_name = 'class enrollment'
        verbose_name_plural = 'class enrollments'
        constraints = [
            models.UniqueConstraint(
                fields=['student'],
                condition=Q(status='active'),
                name='one_active_class_per_student',
            ),
        ]

    def __str__(self):
        return f'{self.student} in {self.klass} ({self.status})'


class Homework(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CLOSED = 'closed', 'Closed'

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='homework',
    )
    klass = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='homework',
    )
    subject = models.CharField(max_length=80)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_date', 'due_date', 'title']
        verbose_name = 'homework'
        verbose_name_plural = 'homework'
        constraints = [
            models.CheckConstraint(
                check=Q(due_date__gte=models.F('assigned_date')),
                name='homework_due_date_on_or_after_assigned_date',
            ),
        ]

    def __str__(self):
        return f'{self.title} - {self.klass}'


class HomeworkSubmission(models.Model):
    class SubmissionStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUBMITTED = 'submitted', 'Submitted'
        LATE = 'late', 'Late'

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='homework_submissions',
    )
    submission_notes = models.TextField(blank=True)
    submission_status = models.CharField(
        max_length=10,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    grade = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['homework__due_date', 'student__full_name']
        verbose_name = 'homework submission'
        verbose_name_plural = 'homework submissions'
        unique_together = ('homework', 'student')

    def __str__(self):
        return f'{self.student} - {self.homework} ({self.submission_status})'
