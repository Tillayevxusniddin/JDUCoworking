# apps/reports/permissions.py

from rest_framework import permissions

class IsStudent(permissions.BasePermission):
    """Checking Requesting user must be a 'STUDENT'."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'STUDENT'

class IsStaffOrAdmin(permissions.BasePermission):
    """Checking Requesting user must be 'STAFF' or 'ADMIN'."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ['STAFF', 'ADMIN']

class IsOwnerOrStaffAdmin(permissions.BasePermission):
    """
    Object owner or Staff/Admin permission.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'student'):
            if request.user.user_type in ['STAFF', 'ADMIN']:
                return True
            return obj.student == request.user
        return False