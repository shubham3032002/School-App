from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from student.models import Student
from .models import Quiz, QuizQuestion, QuizSubmission, QuizAnswer
from .permissions import IsAssignedQuizTeacher
from .serializers import (
    QuizReadSerializer,
    QuizWriteSerializer,
    QuizStudentReadSerializer,
    QuizQuestionWriteSerializer,
    QuizQuestionReadSerializer,
    QuizSubmissionReadSerializer,
    QuizSubmitSerializer,
)


# ─────────────────────────────────────────────
# Helper — decode student JWT
# (self-contained; mirrors homework app pattern exactly)
# ─────────────────────────────────────────────

def get_student_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationFailed('Bearer token required.')
    try:
        token = AccessToken(auth_header.split(' ')[1])
    except Exception:
        raise AuthenticationFailed('Token is invalid or expired.')
    if token.get('type') != 'student':
        raise AuthenticationFailed('Not a student token.')
    try:
        return Student.objects.select_related('class_id').get(id=token.get('student_id'))
    except Student.DoesNotExist:
        raise AuthenticationFailed('Student not found.')


# ─────────────────────────────────────────────
# Teacher — Quiz CRUD
# ─────────────────────────────────────────────

class QuizListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/quiz/
        Teacher  → their own quizzes only
        Admin / Principal → all quizzes
        Query params: ?klass=<id>  ?subject=<str>  ?status=<draft|published|closed>

    POST /api/quiz/
        Teacher creates a quiz for a class they are assigned to teach.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return QuizWriteSerializer if self.request.method == 'POST' else QuizReadSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'request': self.request}

    def get_queryset(self):
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)

        if user.role in ['admin', 'principal']:
            qs = (Quiz.objects
                  .select_related('teacher__user', 'klass')
                  .prefetch_related('questions')
                  .all())
        elif teacher:
            qs = (Quiz.objects
                  .select_related('teacher__user', 'klass')
                  .prefetch_related('questions')
                  .filter(teacher=teacher))
        else:
            return Quiz.objects.none()

        klass_id  = self.request.query_params.get('klass')
        subject   = self.request.query_params.get('subject')
        qz_status = self.request.query_params.get('status')
        if klass_id:  qs = qs.filter(klass_id=klass_id)
        if subject:   qs = qs.filter(subject__icontains=subject)
        if qz_status: qs = qs.filter(status=qz_status)
        return qs

    def perform_create(self, serializer):
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)

        # Admin / principal can create on behalf of any teacher
        if user.role in ['admin', 'principal']:
            serializer.save()
            return

        if teacher is None:
            raise PermissionDenied('Only teachers can create quizzes.')

        klass = serializer.validated_data.get('klass')

        # Teacher must be assigned to teach that class
        from teacher.models import TeacherClassAssignment
        if not TeacherClassAssignment.objects.filter(teacher=teacher, klass=klass).exists():
            raise PermissionDenied('You can only assign quizzes to classes you teach.')

        # Teacher cannot create a quiz under another teacher's name
        if serializer.validated_data.get('teacher') != teacher:
            raise PermissionDenied('You can only create quizzes under your own name.')

        serializer.save()


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/quiz/<id>/   — full quiz detail with questions + correct answers (teacher view)
    PATCH  /api/quiz/<id>/   — update quiz metadata (title, dates, status, etc.)
    DELETE /api/quiz/<id>/   — delete quiz (cascades to questions, submissions, answers)
    """
    permission_classes = [IsAuthenticated, IsAssignedQuizTeacher]

    def get_serializer_class(self):
        return QuizWriteSerializer if self.request.method in ['PUT', 'PATCH'] else QuizReadSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'request': self.request}

    def get_queryset(self):
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)
        if user.role in ['admin', 'principal']:
            return (Quiz.objects
                    .select_related('teacher__user', 'klass')
                    .prefetch_related('questions')
                    .all())
        if teacher:
            return (Quiz.objects
                    .select_related('teacher__user', 'klass')
                    .prefetch_related('questions')
                    .filter(teacher=teacher))
        return Quiz.objects.none()


# ─────────────────────────────────────────────
# Teacher — Question CRUD (nested under a quiz)
# ─────────────────────────────────────────────

class QuizQuestionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/quiz/<quiz_id>/questions/   — list all questions for the quiz
    POST /api/quiz/<quiz_id>/questions/   — add a new question to the quiz
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return QuizQuestionWriteSerializer if self.request.method == 'POST' else QuizQuestionReadSerializer

    def _get_quiz(self):
        """Fetch the parent quiz and enforce teacher ownership."""
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)
        quiz    = get_object_or_404(Quiz, pk=self.kwargs['quiz_id'])
        if user.role not in ['admin', 'principal']:
            if teacher is None or quiz.teacher != teacher:
                raise PermissionDenied('You can only manage questions for your own quizzes.')
        return quiz

    def get_queryset(self):
        return self._get_quiz().questions.all()

    def perform_create(self, serializer):
        quiz = self._get_quiz()
        serializer.save(quiz=quiz)


class QuizQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/quiz/<quiz_id>/questions/<pk>/   — retrieve one question
    PATCH  /api/quiz/<quiz_id>/questions/<pk>/   — update question text / options / answer
    DELETE /api/quiz/<quiz_id>/questions/<pk>/   — delete question
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return QuizQuestionWriteSerializer if self.request.method in ['PUT', 'PATCH'] else QuizQuestionReadSerializer

    def get_queryset(self):
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)
        quiz    = get_object_or_404(Quiz, pk=self.kwargs['quiz_id'])
        if user.role not in ['admin', 'principal']:
            if teacher is None or quiz.teacher != teacher:
                raise PermissionDenied('You can only manage questions for your own quizzes.')
        return quiz.questions.all()


# ─────────────────────────────────────────────
# Teacher — view all submissions for a quiz
# ─────────────────────────────────────────────

class QuizSubmissionsView(generics.ListAPIView):
    """
    GET /api/quiz/<quiz_id>/submissions/
    Returns every student submission for the quiz with per-answer breakdown and scores.
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = QuizSubmissionReadSerializer

    def get_queryset(self):
        quiz    = get_object_or_404(Quiz, pk=self.kwargs['quiz_id'])
        user    = self.request.user
        teacher = getattr(user, 'teacher_profile', None)

        if user.role not in ['admin', 'principal']:
            if teacher is None or quiz.teacher != teacher:
                raise PermissionDenied('You can only view submissions for your own quizzes.')

        return (QuizSubmission.objects
                .select_related('student', 'quiz__klass')
                .prefetch_related('answers__question')
                .filter(quiz=quiz))

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'request': self.request}


# ─────────────────────────────────────────────
# Student — view published quizzes
# ─────────────────────────────────────────────

class StudentQuizListView(APIView):
    """
    GET /api/quiz/student/my-quizzes/

    Returns all PUBLISHED quizzes assigned to the student's class.
    Questions are included but correct_option is hidden from this response.
    """
    permission_classes     = []
    authentication_classes = []

    def get(self, request):
        student = get_student_from_token(request)

        if student.class_id is None:
            return Response(
                {'detail': 'You are not assigned to any class.'},
                status=status.HTTP_200_OK,
            )

        quizzes = (Quiz.objects
                   .select_related('klass')
                   .prefetch_related('questions')
                   .filter(klass=student.class_id, status=Quiz.Status.PUBLISHED)
                   .order_by('-assigned_date'))

        serializer = QuizStudentReadSerializer(quizzes, many=True)
        return Response({
            'class':   student.class_id.name,
            'total':   quizzes.count(),
            'quizzes': serializer.data,
        })


# ─────────────────────────────────────────────
# Student — submit a quiz
# ─────────────────────────────────────────────

class StudentSubmitQuizView(APIView):
    """
    POST /api/quiz/<quiz_id>/submit/
    Content-Type: application/json

    Body:
    {
        "answers": [
            {"question_id": 1, "selected_option": "B"},
            {"question_id": 2, "selected_option": "A"},
            ...
        ]
    }

    Behaviour:
    ─ Validates every question_id belongs to this quiz.
    ─ Auto-grades each answer (is_correct) and sums the score.
    ─ Marks the submission LATE if submitted after quiz due_date.
    ─ Re-submission is allowed: old answers are deleted and score is recalculated.
    """
    permission_classes     = []
    authentication_classes = []

    def post(self, request, quiz_id):
        student = get_student_from_token(request)
        quiz    = get_object_or_404(Quiz, pk=quiz_id, status=Quiz.Status.PUBLISHED)

        # Student must belong to the quiz's class
        if student.class_id != quiz.klass:
            return Response(
                {'detail': 'This quiz is not assigned to your class.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate payload structure
        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers_data = serializer.validated_data['answers']

        # Validate all submitted question IDs actually belong to this quiz
        question_ids    = [a['question_id'] for a in answers_data]
        valid_questions = {q.id: q for q in quiz.questions.filter(id__in=question_ids)}
        invalid_ids     = set(question_ids) - set(valid_questions.keys())
        if invalid_ids:
            raise ValidationError({
                'answers': f'Invalid question IDs for this quiz: {sorted(invalid_ids)}'
            })

        # ── Auto-grade ────────────────────────────────────────
        total_marks = sum(q.marks for q in valid_questions.values())
        score       = 0
        answer_objs = []

        for a in answers_data:
            q          = valid_questions[a['question_id']]
            is_correct = (a['selected_option'] == q.correct_option)
            if is_correct:
                score += q.marks
            answer_objs.append({
                'question':        q,
                'selected_option': a['selected_option'],
                'is_correct':      is_correct,
            })

        # ── Determine late / on-time ──────────────────────────
        submitted_at      = timezone.now()
        submission_status = (
            QuizSubmission.SubmissionStatus.LATE
            if submitted_at.date() > quiz.due_date
            else QuizSubmission.SubmissionStatus.SUBMITTED
        )

        # ── Upsert submission record ──────────────────────────
        submission, created = QuizSubmission.objects.update_or_create(
            quiz=quiz,
            student=student,
            defaults={
                'submission_status': submission_status,
                'submitted_at':      submitted_at,
                'score':             score,
                'total_marks':       total_marks,
            },
        )

        # Replace all previous answers on re-submission
        submission.answers.all().delete()
        QuizAnswer.objects.bulk_create([
            QuizAnswer(
                submission      = submission,
                question        = a['question'],
                selected_option = a['selected_option'],
                is_correct      = a['is_correct'],
            )
            for a in answer_objs
        ])

        out = QuizSubmissionReadSerializer(submission)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────
# Student — view own submissions
# ─────────────────────────────────────────────

class StudentMyQuizSubmissionsView(APIView):
    """
    GET /api/quiz/student/my-submissions/

    Returns all quiz submissions made by the authenticated student,
    including per-answer breakdown and percentage score.
    """
    permission_classes     = []
    authentication_classes = []

    def get(self, request):
        student = get_student_from_token(request)

        submissions = (QuizSubmission.objects
                       .select_related('quiz__klass')
                       .prefetch_related('answers__question')
                       .filter(student=student)
                       .order_by('-quiz__due_date'))

        serializer = QuizSubmissionReadSerializer(submissions, many=True)
        return Response({'total': submissions.count(), 'submissions': serializer.data})