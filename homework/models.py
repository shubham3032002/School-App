from django.db import models
from django.utils import timezone
from teacher.models import Class, Teacher
from student.models import Student


def homework_image_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f"homework_images/{instance.pk or 'new'}/{filename}"


def homework_submission_image_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f"homework_submissions/{instance.homework_id}/{instance.student_id}.{ext}"


class Homework(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        PUBLISHED = 'published', 'Published'
        CLOSED    = 'closed',    'Closed'

    teacher        = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='hw_assigned')
    klass          = models.ForeignKey(Class,   on_delete=models.CASCADE, related_name='hw_homework')
    subject        = models.CharField(max_length=80)
    title          = models.CharField(max_length=200)
    description    = models.TextField(blank=True)
    assigned_date  = models.DateField(default=timezone.localdate)
    due_date       = models.DateField()
    status         = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at     = models.DateTimeField(auto_now_add=True)
    homework_image = models.ImageField(
        upload_to=homework_image_path,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-assigned_date', 'due_date']
        verbose_name = 'homework'
        verbose_name_plural = 'homework'
        constraints = [
            models.CheckConstraint(
                check=models.Q(due_date__gte=models.F('assigned_date')),
                name='hw_due_date_on_or_after_assigned_date',
            )
        ]

    def __str__(self):
        return f"{self.title} — {self.klass} ({self.status})"


class HomeworkSubmission(models.Model):
    class SubmissionStatus(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        SUBMITTED = 'submitted', 'Submitted'
        LATE      = 'late',      'Late'

    homework          = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='hw_submissions')
    student           = models.ForeignKey(Student,  on_delete=models.CASCADE, related_name='hw_submissions')
    submission_notes  = models.TextField(blank=True)
    submission_status = models.CharField(max_length=10, choices=SubmissionStatus.choices, default=SubmissionStatus.PENDING)
    submitted_at      = models.DateTimeField(null=True, blank=True)
    grade             = models.PositiveSmallIntegerField(null=True, blank=True)
    submission_image  = models.ImageField(
        upload_to=homework_submission_image_path,
        null=True,
        blank=True,
    )

    class Meta:
        ordering        = ['homework__due_date', 'student__first_name']
        unique_together = ('homework', 'student')
        verbose_name        = 'homework submission'
        verbose_name_plural = 'homework submissions'

    def __str__(self):
        return f"{self.student} — {self.homework.title} ({self.submission_status})"