from rest_framework.permissions import BasePermission


class IsAssignedQuizTeacher(BasePermission):
    """
    Write access: only the teacher who created the quiz, or admin / principal.
    Read access: passes through (queryset handles class-level scoping).
    """
    message = 'Only the assigned teacher, admin, or principal can perform this action.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ['admin', 'principal']:
            return True
        teacher = getattr(user, 'teacher_profile', None)
        return teacher is not None and obj.teacher == teacher