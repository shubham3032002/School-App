from django.db import models
from django.utils import timezone
from teacher.models import Class, Teacher
from student.models import Student


class Quiz(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        PUBLISHED = 'published', 'Published'
        CLOSED    = 'closed',    'Closed'

    teacher       = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='quizzes')
    klass         = models.ForeignKey(Class,   on_delete=models.CASCADE, related_name='quizzes')
    subject       = models.CharField(max_length=80)
    title         = models.CharField(max_length=200)
    description   = models.TextField(blank=True)
    assigned_date = models.DateField(default=timezone.localdate)
    due_date      = models.DateField()
    status        = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-assigned_date', 'due_date']
        verbose_name        = 'quiz'
        verbose_name_plural = 'quizzes'
        constraints = [
            models.CheckConstraint(
                check=models.Q(due_date__gte=models.F('assigned_date')),
                name='quiz_due_date_on_or_after_assigned_date',
            )
        ]

    def __str__(self):
        return f"{self.title} — {self.klass} ({self.status})"


class QuizQuestion(models.Model):
    """One MCQ question belonging to a quiz, with 4 fixed options (A/B/C/D)."""

    OPTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]

    quiz           = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text  = models.TextField()
    option_a       = models.CharField(max_length=300)
    option_b       = models.CharField(max_length=300)
    option_c       = models.CharField(max_length=300)
    option_d       = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    marks          = models.PositiveSmallIntegerField(default=1)
    order          = models.PositiveSmallIntegerField(default=0)   # display order

    class Meta:
        ordering     = ['order', 'id']
        verbose_name = 'quiz question'

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:60]}"


class QuizSubmission(models.Model):
    """One submission record per student per quiz."""

    class SubmissionStatus(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        SUBMITTED = 'submitted', 'Submitted'
        LATE      = 'late',      'Late'

    quiz              = models.ForeignKey(Quiz,    on_delete=models.CASCADE, related_name='submissions')
    student           = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_submissions')
    submission_status = models.CharField(
        max_length=10,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    score        = models.PositiveSmallIntegerField(null=True, blank=True)   # auto-calculated
    total_marks  = models.PositiveSmallIntegerField(null=True, blank=True)   # snapshot at submit time

    class Meta:
        ordering            = ['quiz__due_date', 'student__first_name']
        unique_together     = ('quiz', 'student')
        verbose_name        = 'quiz submission'
        verbose_name_plural = 'quiz submissions'

    def __str__(self):
        return f"{self.student} — {self.quiz.title} ({self.submission_status})"


class QuizAnswer(models.Model):
    """One row per question per student submission. Auto-graded on save."""

    OPTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]

    submission      = models.ForeignKey(QuizSubmission, on_delete=models.CASCADE, related_name='answers')
    question        = models.ForeignKey(QuizQuestion,   on_delete=models.CASCADE, related_name='answers')
    selected_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    is_correct      = models.BooleanField(default=False)   # set automatically on save

    class Meta:
        unique_together = ('submission', 'question')
        verbose_name    = 'quiz answer'

    def save(self, *args, **kwargs):
        # Auto-grade: compare student's choice with the stored correct option
        self.is_correct = (self.selected_option == self.question.correct_option)
        super().save(*args, **kwargs)

    def __str__(self):
        tick = '✓' if self.is_correct else '✗'
        return f"{self.submission.student} | Q{self.question.order} → {self.selected_option} ({tick})"