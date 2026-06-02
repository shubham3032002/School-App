from rest_framework.permissions import BasePermission


def user_has_role(user, roles):
    return bool(user and user.is_authenticated and getattr(user, 'role', None) in roles)


class IsTeacherOrAbove(BasePermission):
    """Allow authenticated staff, manager, head, and admin users."""

    def has_permission(self, request, view):
        return user_has_role(request.user, ['staff', 'manager', 'head', 'admin'])


class IsManagerOrAbove(BasePermission):
    """Allow authenticated manager, head, and admin users."""

    def has_permission(self, request, view):
        return user_has_role(request.user, ['manager', 'head', 'admin'])


class IsOwnerTeacher(BasePermission):
    """Allow the owner teacher of a resource, or admin/head users."""

    def has_object_permission(self, request, view, obj):
        if user_has_role(request.user, ['admin', 'head']):
            return True

        teacher = getattr(request.user, 'teacher_profile', None)
        if teacher is None:
            return False

        resource_teacher = getattr(obj, 'teacher', None)
        if resource_teacher is None and hasattr(obj, 'homework'):
            resource_teacher = obj.homework.teacher
        if resource_teacher is None and hasattr(obj, 'enrolled_by'):
            resource_teacher = obj.enrolled_by

        return resource_teacher == teacher
