"""
Role-based permission classes for the CDA unified backend.

Usage:
    from core.permissions import HasRole, IsStudentOrParent

    class MyView(APIView):
        permission_classes = [HasRole("instructor")]

    class AnotherView(APIView):
        permission_classes = [IsStudentOrParent]

The HasRole factory returns a permission class that checks the user's
`role` field. For compound checks, use the pre-built classes below or
compose with `|` (OR) and `&` (AND).
"""

from rest_framework.permissions import BasePermission


def HasRole(*allowed_roles):
    """
    Factory that returns a permission class allowing only users whose
    `role` is in `allowed_roles`.

    Example:
        permission_classes = [HasRole("instructor", "admin")]
    """

    class _RolePermission(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            return request.user.role in allowed_roles

    # Give the class a readable name for DRF's error messages
    _RolePermission.__name__ = f"HasRole_{'_'.join(allowed_roles)}"
    _RolePermission.__qualname__ = _RolePermission.__name__
    return _RolePermission


# Pre-built compound permissions for common patterns

class IsStudentOrParent(BasePermission):
    """Allow students and parents."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ("student", "parent")


class IsInstructorOrAdmin(BasePermission):
    """Allow instructors and admins."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ("instructor", "admin")


class IsAdmin(BasePermission):
    """Allow only admins."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == "admin"
