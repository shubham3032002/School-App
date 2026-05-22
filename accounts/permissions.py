from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    roles = ()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(request.user, "role", None)
        return role is not None and role.role in self.roles


class IsStudent(HasRole):
    roles = ("student",)


class IsParent(HasRole):
    roles = ("parent",)


class IsTeacher(HasRole):
    roles = ("teacher",)


class IsPrincipal(HasRole):
    roles = ("principal",)


class IsStaff(HasRole):
    roles = ("staff",)


class IsHead(HasRole):
    roles = ("head",)


class IsPrincipalOrHead(HasRole):
    roles = ("principal", "head")
