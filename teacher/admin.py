from django.contrib import admin

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


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'subject_specialization', 'created_at')
    list_filter = ('subject_specialization', 'created_at')
    search_fields = ('user__email', 'user__fullname', 'phone', 'subject_specialization')


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'grade_level', 'section', 'academic_year', 'homeroom_teacher')
    list_filter = ('academic_year', 'grade_level', 'section')
    search_fields = ('name', 'grade_level', 'section', 'homeroom_teacher__user__fullname')


@admin.register(TeacherClassAssignment)
class TeacherClassAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'klass', 'subject', 'assigned_at')
    list_filter = ('subject', 'assigned_at')
    search_fields = ('teacher__user__fullname', 'klass__name', 'subject')


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'teacher',
        'klass',
        'subject',
        'day_of_week',
        'start_time',
        'end_time',
        'room_number',
        'slot_type',
    )
    list_filter = ('day_of_week', 'slot_type', 'subject')
    search_fields = ('teacher__user__fullname', 'klass__name', 'subject', 'room_number')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'roll_number', 'gender', 'parent_contact', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('full_name', 'roll_number', 'parent_contact')


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'klass', 'status', 'enrollment_date', 'enrolled_by')
    list_filter = ('status', 'enrollment_date', 'klass')
    search_fields = ('student__full_name', 'student__roll_number', 'klass__name')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'teacher', 'klass', 'subject', 'due_date', 'status')
    list_filter = ('status', 'subject', 'assigned_date', 'due_date')
    search_fields = ('title', 'teacher__user__fullname', 'klass__name', 'subject')


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'homework', 'student', 'submission_status', 'submitted_at', 'grade')
    list_filter = ('submission_status', 'submitted_at', 'grade')
    search_fields = ('homework__title', 'student__full_name', 'student__roll_number')
