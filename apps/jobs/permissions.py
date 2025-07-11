# apps/jobs/permissions.py
from rest_framework import permissions

class IsApplicantOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.user_type in ['STAFF', 'ADMIN']:
            return True
        return obj.applicant == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 'ADMIN':
            return True
        return request.method in permissions.SAFE_METHODS