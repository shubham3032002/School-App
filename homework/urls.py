from django.urls import path
from .views import (
    HomeworkListCreateView,
    HomeworkDetailView,
    HomeworkSubmissionsView,
    GradeSubmissionView,
    StudentHomeworkListView,
    StudentSubmitHomeworkView,
    StudentMySubmissionsView,
)

urlpatterns = [
    # ── Teacher endpoints ──────────────────────────────────────
    path('',                                        HomeworkListCreateView.as_view(),  name='homework-list'),
    path('<int:pk>/',                               HomeworkDetailView.as_view(),       name='homework-detail'),
    path('<int:homework_id>/submissions/',          HomeworkSubmissionsView.as_view(),  name='homework-submissions'),
    path('submissions/<int:pk>/grade/',             GradeSubmissionView.as_view(),      name='homework-grade'),

    # ── Student endpoints (student JWT) ───────────────────────
    path('student/my-homework/',                    StudentHomeworkListView.as_view(),  name='student-homework'),
    path('student/my-submissions/',                 StudentMySubmissionsView.as_view(), name='student-submissions'),
    path('<int:homework_id>/submit/',               StudentSubmitHomeworkView.as_view(), name='homework-submit'),
]