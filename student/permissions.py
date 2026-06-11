from rest_framework.permissions import BasePermission


class IsAdminOrHead(BasePermission):
    """Only admin, head teacher, or principal can manage students."""
    message = 'Only admin or head users can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'head_teacher', 'principal']
        )


class IsTeacher(BasePermission):
    """User must have a teacher profile to access attendance endpoints."""
    message = 'You must be a teacher to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'teacher_profile')
        )


class IsHomeroomTeacher(BasePermission):
    """Only the homeroom teacher of the class can mark or edit attendance."""
    message = 'Only the homeroom teacher of this class can mark attendance.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'teacher_profile')
        )

    def has_object_permission(self, request, view, obj):
        teacher = request.user.teacher_profile
        return obj.klass.homeroom_teacher == teacher