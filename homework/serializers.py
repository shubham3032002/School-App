from rest_framework import serializers
from .models import Homework, HomeworkSubmission

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


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
            'submission_image',
        ]
        read_only_fields = ['id']

    def validate_grade(self, value):
        if value is not None and value > 100:
            raise serializers.ValidationError('Grade must be between 0 and 100.')
        return value

    def validate_submission_image(self, value):
        if value:
            if value.content_type not in ALLOWED_IMAGE_TYPES:
                raise serializers.ValidationError('Only JPEG, PNG, WEBP, or GIF images are allowed.')
            if value.size > MAX_IMAGE_SIZE_BYTES:
                raise serializers.ValidationError('Image must be smaller than 5 MB.')
        return value


class HomeworkSubmissionReadSerializer(serializers.ModelSerializer):
    student_name         = serializers.SerializerMethodField()
    homework_title       = serializers.CharField(source='homework.title',      read_only=True)
    class_name           = serializers.CharField(source='homework.klass.name', read_only=True)
    submission_image_url = serializers.SerializerMethodField()

    class Meta:
        model  = HomeworkSubmission
        fields = [
            'id', 'homework', 'homework_title', 'class_name',
            'student', 'student_name',
            'submission_notes', 'submission_status', 'submitted_at', 'grade',
            'submission_image_url',
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_submission_image_url(self, obj):
        if not obj.submission_image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.submission_image.url) if request else obj.submission_image.url