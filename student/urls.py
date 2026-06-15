from django.urls import path

from .views import (
    AttendanceDetailView,
    AttendanceListCreateView,
    AttendanceSummaryView,
    BulkAttendanceView,
    ClassStudentsView,
    StudentDetailView,
    StudentListCreateView,
    StudentLoginView,
    StudentChangePasswordView,
    StudentProfileView
)

urlpatterns = [
    # ── Student CRUD ──────────────────────────────────────────
    path('',          StudentListCreateView.as_view(), name='student-list'),
    path('<int:pk>/', StudentDetailView.as_view(),     name='student-detail'),

    # ── Attendance ────────────────────────────────────────────
    path('attendance/',          AttendanceListCreateView.as_view(), name='attendance-list'),
    path('attendance/<int:pk>/', AttendanceDetailView.as_view(),     name='attendance-detail'),
    path('attendance/bulk/',     BulkAttendanceView.as_view(),       name='attendance-bulk'),
    path('attendance/summary/',  AttendanceSummaryView.as_view(),    name='attendance-summary'),

    # ── Helpers ───────────────────────────────────────────────
    path('classes/<int:klass_id>/students/', ClassStudentsView.as_view(), name='class-students'),
     path('login/',           StudentLoginView.as_view(),          name='student-login'),
    path('change-password/', StudentChangePasswordView.as_view(), name='student-change-password'),
    path('students/me/', StudentProfileView.as_view(), name='student-profile'),

]