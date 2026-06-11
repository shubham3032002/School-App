from django.urls import path
from .views import (
    StudentListCreateView,
    StudentDetailView,
    AttendanceListCreateView,
    AttendanceDetailView,
    BulkAttendanceView,
    ClassStudentsView,
    AttendanceSummaryView,
)

urlpatterns = [
    # ── Student CRUD ──────────────────────────────────────────
    path('students/',          StudentListCreateView.as_view(), name='student-list'),
    path('students/<int:pk>/', StudentDetailView.as_view(),     name='student-detail'),

    # ── Attendance ────────────────────────────────────────────
    path('attendance/',          AttendanceListCreateView.as_view(), name='attendance-list'),
    path('attendance/<int:pk>/', AttendanceDetailView.as_view(),     name='attendance-detail'),
    path('attendance/bulk/',     BulkAttendanceView.as_view(),       name='attendance-bulk'),
    path('attendance/summary/',  AttendanceSummaryView.as_view(),    name='attendance-summary'),

    # ── Helpers ───────────────────────────────────────────────
    path('classes/<int:klass_id>/students/', ClassStudentsView.as_view(), name='class-students'),
]