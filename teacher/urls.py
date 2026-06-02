from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ClassEnrollmentViewSet,
    ClassViewSet,
    HomeworkSubmissionViewSet,
    HomeworkViewSet,
    StudentViewSet,
    TeacherClassAssignmentViewSet,
    TeacherViewSet,
    TimetableSlotViewSet,
)


router = DefaultRouter()
router.register('teachers', TeacherViewSet, basename='teacher')
router.register('classes', ClassViewSet, basename='class')
router.register('assignments', TeacherClassAssignmentViewSet, basename='teacher-assignment')
router.register('timetable', TimetableSlotViewSet, basename='timetable')
router.register('students', StudentViewSet, basename='student')
router.register('enrollments', ClassEnrollmentViewSet, basename='enrollment')
router.register('homework', HomeworkViewSet, basename='homework')
router.register('submissions', HomeworkSubmissionViewSet, basename='homework-submission')

grade_submission = HomeworkViewSet.as_view({'patch': 'grade_submission'})

urlpatterns = [
    path(
        'homework/<int:homework_pk>/submissions/<int:submission_id>/grade/',
        grade_submission,
        name='homework-grade-submission',
    ),
]

urlpatterns += router.urls
