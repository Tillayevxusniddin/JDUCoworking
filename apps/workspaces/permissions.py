from rest_framework import permissions
from .models import WorkspaceMember, Workspace

class IsAdminUserType(permissions.BasePermission):
    
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'user_type', None) == 'ADMIN')
    
class IsWorkspaceMember(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'user_type', None) == 'ADMIN':
            return True
        return WorkspaceMember.objects.filter(workspace=obj, user=user, is_active=True).exists()
    
class IsAdminOrWorkspaceMemberReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
             return bool(user and user.is_authenticated)
        return bool(user and user.is_authenticated and getattr(user, 'user_type', None) == 'ADMIN')
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            if getattr(user, 'user_type', None) == 'ADMIN':
                return True
            return WorkspaceMember.objects.filter(workspace=obj, user=user, is_active=True).exists()
        
        return getattr(user, 'user_type', None) == 'ADMIN'
