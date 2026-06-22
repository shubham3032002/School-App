from django.contrib import admin
from .models import Homework, HomeworkSubmission


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display  = ('id', 'title', 'teacher', 'klass', 'subject', 'due_date', 'status')
    list_filter   = ('status', 'subject', 'assigned_date')
    search_fields = ('title', 'teacher__user__fullname', 'klass__name', 'subject')


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'homework', 'student', 'submission_status', 'submitted_at', 'grade')
    list_filter   = ('submission_status',)
    search_fields = ('homework__title', 'student__first_name', 'student__admission_number')