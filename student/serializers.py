from rest_framework import serializers
from django.utils import timezone
from .models import Student, AttendanceRecord


class StudentWriteSerializer(serializers.ModelSerializer):
    """Used for creating and updating students."""

    class Meta:
        model  = Student
        fields = [
            'id',
            'admission_number',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'class_id',
            'section',
            'roll_number',
            'address',
            'phone',
            'email',
            'guardian_name',
            'guardian_phone',
        ]
        read_only_fields = ['id']

    def validate_date_of_birth(self, value):
        # Cannot be in the future
        if value > timezone.localdate():
            raise serializers.ValidationError('Date of birth cannot be in the future.')
        return value

    def validate_admission_number(self, value):
        # Must be unique — exclude self on update
        qs = Student.objects.filter(admission_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Admission number already exists.')
        return value

    def validate_email(self, value):
        # Email must be unique if provided — exclude self on update
        if not value:
            return value
        qs = Student.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Email already exists.')
        return value


class StudentReadSerializer(serializers.ModelSerializer):
    """Used for listing and retrieving students with extra info."""

    class_name = serializers.CharField(source='class_id.name', read_only=True, default=None)
    full_name  = serializers.SerializerMethodField()

    class Meta:
        model  = Student
        fields = [
            'id',
            'admission_number',
            'first_name',
            'last_name',
            'full_name',
            'gender',
            'date_of_birth',
            'class_id',
            'class_name',
            'section',
            'roll_number',
            'address',
            'phone',
            'email',
            'guardian_name',
            'guardian_phone',
            'created_at',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class AttendanceWriteSerializer(serializers.ModelSerializer):
    """Used for creating and updating a single attendance record."""

    class Meta:
        model  = AttendanceRecord
        fields = [
            'id',
            'student',
            'klass',
            'teacher',
            'attendance_date',
            'status',
            'remarks',
        ]
        # Teacher is set automatically from logged-in user
        read_only_fields = ['id', 'teacher']

    def validate_attendance_date(self, value):
        # Cannot mark attendance for future dates
        if value > timezone.localdate():
            raise serializers.ValidationError('Attendance date cannot be in the future.')
        return value

    def validate(self, attrs):
        klass   = attrs.get('klass')
        student = attrs.get('student')

        # Student must belong to this class
        if student.class_id != klass:
            raise serializers.ValidationError(
                'This student is not enrolled in the selected class.'
            )
        return attrs


class AttendanceReadSerializer(serializers.ModelSerializer):
    """Used for listing and retrieving attendance with readable names."""

    student_name = serializers.SerializerMethodField()
    student_roll = serializers.CharField(source='student.roll_number', read_only=True)
    class_name   = serializers.CharField(source='klass.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.fullname', read_only=True)

    class Meta:
        model  = AttendanceRecord
        fields = [
            'id',
            'student',
            'student_name',
            'student_roll',
            'klass',
            'class_name',
            'teacher',
            'teacher_name',
            'attendance_date',
            'status',
            'remarks',
            'created_at',
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Mark attendance for ALL students in a class at once.
    Payload:
    {
        "klass": 1,
        "attendance_date": "2026-06-11",
        "records": [
            {"student": 1, "status": "Present", "remarks": ""},
            {"student": 2, "status": "Absent",  "remarks": "sick"}
        ]
    }
    """

    klass           = serializers.IntegerField()
    attendance_date = serializers.DateField()
    records         = serializers.ListField(child=serializers.DictField())

    def validate_attendance_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('Attendance date cannot be in the future.')
        return value

    def validate_records(self, value):
        valid_statuses = [s[0] for s in AttendanceRecord.Status.choices]
        for record in value:
            if 'student' not in record:
                raise serializers.ValidationError('Each record must have a student id.')
            if 'status' not in record:
                raise serializers.ValidationError('Each record must have a status.')
            if record['status'] not in valid_statuses:
                raise serializers.ValidationError(
                    f"Invalid status '{record['status']}'. Valid: {valid_statuses}"
                )
        return value