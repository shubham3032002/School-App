from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizSubmission, QuizAnswer


# ── Inlines ───────────────────────────────────────────────────

class QuizQuestionInline(admin.TabularInline):
    model       = QuizQuestion
    extra       = 1
    fields      = ['order', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'marks']
    ordering    = ['order']


class QuizAnswerInline(admin.TabularInline):
    model           = QuizAnswer
    extra           = 0
    readonly_fields = ['question', 'selected_option', 'is_correct']
    can_delete      = False

    def has_add_permission(self, request, obj=None):
        return False


# ── ModelAdmins ───────────────────────────────────────────────

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display   = ['title', 'teacher', 'klass', 'subject', 'assigned_date', 'due_date', 'status', 'created_at']
    list_filter    = ['status', 'subject', 'klass']
    search_fields  = ['title', 'description', 'teacher__user__fullname']
    ordering       = ['-assigned_date']
    readonly_fields = ['created_at']
    inlines        = [QuizQuestionInline]

    fieldsets = (
        (None, {
            'fields': ('teacher', 'klass', 'subject', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('assigned_date', 'due_date', 'status', 'created_at')
        }),
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display  = ['quiz', 'order', 'question_text', 'correct_option', 'marks']
    list_filter   = ['quiz__klass', 'correct_option']
    search_fields = ['question_text', 'quiz__title']
    ordering      = ['quiz', 'order']


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display   = ['student', 'quiz', 'submission_status', 'submitted_at', 'score', 'total_marks']
    list_filter    = ['submission_status', 'quiz__klass']
    search_fields  = ['student__first_name', 'student__last_name', 'quiz__title']
    ordering       = ['-submitted_at']
    readonly_fields = ['submitted_at', 'score', 'total_marks', 'submission_status']
    inlines        = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display  = ['submission', 'question', 'selected_option', 'is_correct']
    list_filter   = ['is_correct', 'selected_option']
    search_fields = ['submission__student__first_name', 'question__question_text']
    readonly_fields = ['is_correct']