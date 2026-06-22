from rest_framework import serializers
from django.utils import timezone
from .models import Homework, HomeworkSubmission


class HomeworkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Homework
        fields = [
            'id', 'teacher', 'klass', 'subject',
            'title', 'description', 'assigned_date', 'due_date', 'status',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        assigned_date = attrs.get('assigned_date', getattr(self.instance, 'assigned_date', None))
        due_date      = attrs.get('due_date',      getattr(self.instance, 'due_date',      None))
        if assigned_date and due_date and due_date < assigned_date:
            raise serializers.ValidationError({'due_date': 'Due date must be on or after assigned date.'})
        return attrs


class HomeworkReadSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.fullname', read_only=True)
    class_name   = serializers.CharField(source='klass.name',            read_only=True)

    class Meta:
        model  = Homework
        fields = [
            'id', 'teacher', 'teacher_name', 'klass', 'class_name',
            'subject', 'title', 'description',
            'assigned_date', 'due_date', 'status', 'created_at',
        ]


class HomeworkSubmissionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = HomeworkSubmission
        fields = [
            'id', 'homework', 'student',
            'submission_notes', 'submission_status', 'submitted_at', 'grade',
        ]
        read_only_fields = ['id']

    def validate_grade(self, value):
        if value is not None and value > 100:
            raise serializers.ValidationError('Grade must be between 0 and 100.')
        return value


class HomeworkSubmissionReadSerializer(serializers.ModelSerializer):
    student_name   = serializers.SerializerMethodField()
    homework_title = serializers.CharField(source='homework.title',      read_only=True)
    class_name     = serializers.CharField(source='homework.klass.name', read_only=True)

    class Meta:
        model  = HomeworkSubmission
        fields = [
            'id', 'homework', 'homework_title', 'class_name',
            'student', 'student_name',
            'submission_notes', 'submission_status', 'submitted_at', 'grade',
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"