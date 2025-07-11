# apps/users/permissions.py

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """Only allows access to users with 'ADMIN' user type."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'ADMIN'

class IsStaffUser(permissions.BasePermission):
    """Only allows access to users with 'STAFF' user type."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'STAFF'

class IsRecruiterUser(permissions.BasePermission):
    """Only allows access to users with 'RECRUITER' user type."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'RECRUITER'

class IsStudentUser(permissions.BasePermission):
    """Only allows access to users with 'STUDENT' user type."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'STUDENT'

class IsAdminOrStaff(permissions.BasePermission):
    """Only allows access to users with 'ADMIN' or 'STAFF' user types."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ['ADMIN', 'STAFF']

class IsProfileOwner(permissions.BasePermission):
    """Only allows access to the object owner or admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'ADMIN':
            return True
        if hasattr(obj, 'user'):
            # Check profile models (Student, Staff, Recruiter)
            return obj.user == request.user
        # Check User model
        return obj == request.user