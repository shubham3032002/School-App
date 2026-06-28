from rest_framework import serializers
from .models import Quiz, QuizQuestion, QuizSubmission, QuizAnswer


# ─────────────────────────────────────────────
# Question serializers
# ─────────────────────────────────────────────

class QuizQuestionWriteSerializer(serializers.ModelSerializer):
    """Used by teachers to create / update a question."""

    class Meta:
        model  = QuizQuestion
        fields = [
            'id', 'quiz', 'question_text',
            'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'marks', 'order',
        ]
        read_only_fields = ['id']

    def validate_correct_option(self, value):
        if value not in ('A', 'B', 'C', 'D'):
            raise serializers.ValidationError('correct_option must be A, B, C, or D.')
        return value

    def validate_marks(self, value):
        if value < 1:
            raise serializers.ValidationError('Marks must be at least 1.')
        return value


class QuizQuestionReadSerializer(serializers.ModelSerializer):
    """
    Returned to teachers — includes correct_option.
    """
    class Meta:
        model  = QuizQuestion
        fields = [
            'id', 'question_text',
            'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'marks', 'order',
        ]


class QuizQuestionStudentSerializer(serializers.ModelSerializer):
    """
    Returned to students — correct_option is intentionally excluded.
    """
    class Meta:
        model  = QuizQuestion
        fields = [
            'id', 'question_text',
            'option_a', 'option_b', 'option_c', 'option_d',
            'marks', 'order',
        ]


# ─────────────────────────────────────────────
# Quiz serializers
# ─────────────────────────────────────────────

class QuizWriteSerializer(serializers.ModelSerializer):
    """Used by teachers to create / update a quiz (questions managed separately)."""

    class Meta:
        model  = Quiz
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


class QuizReadSerializer(serializers.ModelSerializer):
    """
    Full quiz detail for teachers — nested questions include correct_option.
    """
    teacher_name    = serializers.CharField(source='teacher.user.fullname', read_only=True)
    class_name      = serializers.CharField(source='klass.name',            read_only=True)
    questions       = QuizQuestionReadSerializer(many=True, read_only=True)
    total_marks     = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model  = Quiz
        fields = [
            'id', 'teacher', 'teacher_name', 'klass', 'class_name',
            'subject', 'title', 'description',
            'assigned_date', 'due_date', 'status', 'created_at',
            'total_marks', 'total_questions', 'questions',
        ]

    def get_total_marks(self, obj):
        return sum(q.marks for q in obj.questions.all())

    def get_total_questions(self, obj):
        return obj.questions.count()


class QuizStudentReadSerializer(serializers.ModelSerializer):
    """
    Quiz detail for students — questions are included but correct_option is hidden.
    """
    class_name      = serializers.CharField(source='klass.name', read_only=True)
    questions       = QuizQuestionStudentSerializer(many=True, read_only=True)
    total_marks     = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model  = Quiz
        fields = [
            'id', 'klass', 'class_name', 'subject',
            'title', 'description', 'assigned_date', 'due_date',
            'total_marks', 'total_questions', 'questions',
        ]

    def get_total_marks(self, obj):
        return sum(q.marks for q in obj.questions.all())

    def get_total_questions(self, obj):
        return obj.questions.count()


# ─────────────────────────────────────────────
# Submission / Answer serializers
# ─────────────────────────────────────────────

class QuizAnswerWriteSerializer(serializers.Serializer):
    """One item inside the submit payload."""
    question_id     = serializers.IntegerField()
    selected_option = serializers.ChoiceField(choices=['A', 'B', 'C', 'D'])


class QuizSubmitSerializer(serializers.Serializer):
    """
    Full submit payload.
    Body: { "answers": [{"question_id": 1, "selected_option": "B"}, ...] }
    """
    answers = QuizAnswerWriteSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError('At least one answer is required.')
        question_ids = [a['question_id'] for a in value]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError('Duplicate question_id entries are not allowed.')
        return value


class QuizAnswerReadSerializer(serializers.ModelSerializer):
    """Per-answer result returned after auto-grading."""
    question_text  = serializers.CharField(source='question.question_text', read_only=True)
    correct_option = serializers.CharField(source='question.correct_option', read_only=True)
    marks          = serializers.IntegerField(source='question.marks',        read_only=True)

    class Meta:
        model  = QuizAnswer
        fields = [
            'question', 'question_text',
            'selected_option', 'correct_option',
            'is_correct', 'marks',
        ]


class QuizSubmissionReadSerializer(serializers.ModelSerializer):
    """Full submission result — used for teacher list view and student response."""
    student_name = serializers.SerializerMethodField()
    quiz_title   = serializers.CharField(source='quiz.title',      read_only=True)
    class_name   = serializers.CharField(source='quiz.klass.name', read_only=True)
    answers      = QuizAnswerReadSerializer(many=True, read_only=True)
    percentage   = serializers.SerializerMethodField()

    class Meta:
        model  = QuizSubmission
        fields = [
            'id', 'quiz', 'quiz_title', 'class_name',
            'student', 'student_name',
            'submission_status', 'submitted_at',
            'score', 'total_marks', 'percentage',
            'answers',
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_percentage(self, obj):
        if obj.total_marks and obj.total_marks > 0 and obj.score is not None:
            return round((obj.score / obj.total_marks) * 100, 2)
        return None