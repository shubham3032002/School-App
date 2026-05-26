from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    AdminActivateUserView,
    AdminChangeRoleView,
    AdminUserDetailView,
    AdminUserListView,
    ChangePasswordView,
    LoginView,
    LogoutView,
    ManagerDashboardView,
    MyProfileView,
    RegisterView,
    StaffResourceView,
)

urlpatterns = [
    # Public auth endpoints.
    path('login/', LoginView.as_view()),
    path('register/', RegisterView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),

    # Logged-in user account endpoints.
    path('logout/', LogoutView.as_view()),
    path('me/', MyProfileView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),

    # Admin/head user management endpoints.
    path('admin/users/', AdminUserListView.as_view()),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view()),
    path('admin/users/<int:pk>/role/', AdminChangeRoleView.as_view()),
    path('admin/users/<int:pk>/activate/', AdminActivateUserView.as_view()),

    # Role-specific pages/resources.
    path('manager/dashboard/', ManagerDashboardView.as_view()),
    path('staff/resource/', StaffResourceView.as_view()),
]
