from rest_framework.permissions import BasePermission


class IsAdminOrHead(BasePermission):
    message = 'Only admin or head users can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'head', 'principal']
        )


class IsTeacher(BasePermission):
    """User must have a teacher profile."""
    message = 'You must be a teacher to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'teacher_profile')
        )


# ✅ NEW: class teacher OR secondary class teacher of the class
class IsClassTeacher(BasePermission):
    """
    Allow access only to the class_teacher or secondary_class_teacher
    of the relevant class.
    Also allows admin and principal.
    """
    message = 'Only the class teacher or secondary class teacher can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (
                request.user.role in ['admin', 'principal'] or
                hasattr(request.user, 'teacher_profile')
            )
        )

    def has_object_permission(self, request, view, obj):
        if request.user.role in ['admin', 'principal']:
            return True
        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher is None:
            return False
        klass = getattr(obj, 'klass', None)
        if klass is None:
            return False
        return (
            klass.class_teacher == teacher or
            klass.secondary_class_teacher == teacher
        )


class IsHomeroomTeacher(BasePermission):
    """Legacy — kept for backward compat."""
    message = 'Only the homeroom teacher of this class can mark attendance.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'teacher_profile')
        )

    def has_object_permission(self, request, view, obj):
        teacher = request.user.teacher_profile
        return obj.klass.homeroom_teacher == teacher