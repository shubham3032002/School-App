from django.urls import path
from .views import (
    QuizListCreateView,
    QuizDetailView,
    QuizQuestionListCreateView,
    QuizQuestionDetailView,
    QuizSubmissionsView,
    StudentQuizListView,
    StudentSubmitQuizView,
    StudentMyQuizSubmissionsView,
)

urlpatterns = [
    # ── Teacher — Quiz CRUD ────────────────────────────────────────────────────
    # GET  /api/quiz/          → list own quizzes  (?klass= &subject= &status=)
    # POST /api/quiz/          → create a quiz
    path('',                                    QuizListCreateView.as_view(),          name='quiz-list'),

    # GET    /api/quiz/<id>/   → retrieve quiz + questions (with correct answers)
    # PATCH  /api/quiz/<id>/   → update quiz metadata
    # DELETE /api/quiz/<id>/   → delete quiz (cascades questions & submissions)
    path('<int:pk>/',                           QuizDetailView.as_view(),              name='quiz-detail'),

    # ── Teacher — Question CRUD (nested under a quiz) ──────────────────────────
    # GET  /api/quiz/<quiz_id>/questions/         → list questions
    # POST /api/quiz/<quiz_id>/questions/         → add a question
    path('<int:quiz_id>/questions/',            QuizQuestionListCreateView.as_view(),  name='quiz-questions'),

    # GET    /api/quiz/<quiz_id>/questions/<pk>/  → retrieve one question
    # PATCH  /api/quiz/<quiz_id>/questions/<pk>/  → update question / options / answer
    # DELETE /api/quiz/<quiz_id>/questions/<pk>/  → remove question
    path('<int:quiz_id>/questions/<int:pk>/',   QuizQuestionDetailView.as_view(),      name='quiz-question-detail'),

    # ── Teacher — view submissions ─────────────────────────────────────────────
    # GET /api/quiz/<quiz_id>/submissions/        → all submissions with per-answer results
    path('<int:quiz_id>/submissions/',          QuizSubmissionsView.as_view(),         name='quiz-submissions'),

    # ── Student endpoints (student JWT, no DRF session/token auth) ────────────
    # GET  /api/quiz/student/my-quizzes/          → published quizzes for student's class
    path('student/my-quizzes/',                StudentQuizListView.as_view(),          name='student-quizzes'),

    # GET  /api/quiz/student/my-submissions/      → own submission history with scores
    path('student/my-submissions/',            StudentMyQuizSubmissionsView.as_view(), name='student-quiz-submissions'),

    # POST /api/quiz/<quiz_id>/submit/            → submit / resubmit answers
    path('<int:quiz_id>/submit/',              StudentSubmitQuizView.as_view(),        name='quiz-submit'),
]