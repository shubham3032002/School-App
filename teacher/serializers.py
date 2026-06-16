from django.utils import timezone
from rest_framework import serializers

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


class TeacherWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'user', 'phone', 'subject_specialization']
        read_only_fields = ['id']


class TeacherReadSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_fullname = serializers.CharField(source='user.fullname', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id',
            'user',
            'user_email',
            'user_fullname',
            'user_role',
            'phone',
            'subject_specialization',
            'created_at',
        ]


class ClassWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Class
        fields = [
            'id',
            'name',
            'grade_level',
            'section',
            'academic_year',
            'homeroom_teacher',
            'class_teacher',             
            'secondary_class_teacher',   
        ]
        read_only_fields = ['id']


class ClassReadSerializer(serializers.ModelSerializer):
    homeroom_teacher_name = serializers.CharField(
        source='homeroom_teacher.user.fullname', read_only=True, default=None,
    )
    # ✅ ADD THESE TWO
    class_teacher_name = serializers.CharField(
        source='class_teacher.user.fullname', read_only=True, default=None,
    )
    secondary_class_teacher_name = serializers.CharField(
        source='secondary_class_teacher.user.fullname', read_only=True, default=None,
    )

    class Meta:
        model  = Class
        fields = [
            'id',
            'name',
            'grade_level',
            'section',
            'academic_year',
            'homeroom_teacher',
            'homeroom_teacher_name',
            'class_teacher',                   # ✅ ADD
            'class_teacher_name',              # ✅ ADD
            'secondary_class_teacher',         # ✅ ADD
            'secondary_class_teacher_name',    # ✅ ADD
            'created_at',
        ]


class TeacherClassAssignmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClassAssignment
        fields = ['id', 'teacher', 'klass', 'subject']
        read_only_fields = ['id']


class TeacherClassAssignmentReadSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.fullname', read_only=True)
    class_name = serializers.CharField(source='klass.name', read_only=True)

    class Meta:
        model = TeacherClassAssignment
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'klass',
            'class_name',
            'subject',
            'assigned_at',
        ]


class TimetableSlotWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimetableSlot
        fields = [
            'id',
            'teacher',
            'klass',
            'subject',
            'day_of_week',
            'start_time',
            'end_time',
            'room_number',
            'slot_type',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        start_time = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be later than start time.',
            })
        return attrs


class TimetableSlotReadSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.fullname', read_only=True)
    class_name = serializers.CharField(source='klass.name', read_only=True)

    class Meta:
        model = TimetableSlot
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'klass',
            'class_name',
            'subject',
            'day_of_week',
            'start_time',
            'end_time',
            'room_number',
            'slot_type',
        ]


class StudentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id',
            'full_name',
            'roll_number',
            'date_of_birth',
            'gender',
            'parent_contact',
        ]
        read_only_fields = ['id']

    def validate_date_of_birth(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError('Date of birth cannot be in the future.')
        return value


class StudentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id',
            'full_name',
            'roll_number',
            'date_of_birth',
            'gender',
            'parent_contact',
            'created_at',
        ]


class ClassEnrollmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassEnrollment
        fields = ['id', 'klass', 'student', 'enrolled_by', 'enrollment_date', 'status']
        read_only_fields = ['id']


class ClassEnrollmentReadSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    class_name = serializers.CharField(source='klass.name', read_only=True)
    enrolled_by_name = serializers.CharField(
        source='enrolled_by.user.fullname',
        read_only=True,
        default=None,
    )

    class Meta:
        model = ClassEnrollment
        fields = [
            'id',
            'klass',
            'class_name',
            'student',
            'student_name',
            'enrolled_by',
            'enrolled_by_name',
            'enrollment_date',
            'status',
        ]


class HomeworkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = [
            'id',
            'teacher',
            'klass',
            'subject',
            'title',
            'description',
            'assigned_date',
            'due_date',
            'status',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        assigned_date = attrs.get('assigned_date', getattr(self.instance, 'assigned_date', None))
        due_date = attrs.get('due_date', getattr(self.instance, 'due_date', None))
        if assigned_date and due_date and due_date < assigned_date:
            raise serializers.ValidationError({
                'due_date': 'Due date must be on or after the assigned date.',
            })
        return attrs


class HomeworkReadSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.fullname', read_only=True)
    class_name = serializers.CharField(source='klass.name', read_only=True)

    class Meta:
        model = Homework
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'klass',
            'class_name',
            'subject',
            'title',
            'description',
            'assigned_date',
            'due_date',
            'status',
            'created_at',
        ]


class HomeworkSubmissionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkSubmission
        fields = [
            'id',
            'homework',
            'student',
            'submission_notes',
            'submission_status',
            'submitted_at',
            'grade',
        ]
        read_only_fields = ['id']

    def validate_grade(self, value):
        if value is not None and value > 100:
            raise serializers.ValidationError('Grade must be between 0 and 100.')
        return value


class HomeworkSubmissionReadSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    class_name = serializers.CharField(source='homework.klass.name', read_only=True)

    class Meta:
        model = HomeworkSubmission
        fields = [
            'id',
            'homework',
            'homework_title',
            'class_name',
            'student',
            'student_name',
            'submission_notes',
            'submission_status',
            'submitted_at',
            'grade',
        ]
