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

class IsWorkspaceMembersStaff(permissions.BasePermission):
    """
    Foydalanuvchi ma'lum bir ish maydonining a'zosi ekanligini va
    uning aynan shu ish maydonidagi roli 'STAFF' ekanligini tekshiradi.
    """
    message = "Bu amalni faqat ish maydonidagi 'STAFF' rolidagi a'zolar bajara oladi."

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Tizimga kirmagan foydalanuvchilar uchun ruxsat yo'q
        if not user or not user.is_authenticated:
            return False

        # Global ADMIN har doim ruxsatga ega
        if getattr(user, 'user_type', None) == 'ADMIN':
            return True

        # Obyektdan workspace'ni topamiz.
        # `obj` bu Workspace'ning o'zi bo'lishi mumkin yoki boshqa modelda (masalan, Task)
        # unga ishora qiluvchi `workspace` maydoni bo'lishi mumkin.
        workspace = None
        if isinstance(obj, Workspace):
            workspace = obj
        elif hasattr(obj, 'workspace'):
            workspace = obj.workspace
        
        # Agar workspace topilmasa, ruxsat yo'q
        if not workspace:
            return False

        # Foydalanuvchining shu workspace'dagi a'zoligini va rolini tekshiramiz
        try:
            member = WorkspaceMember.objects.get(workspace=workspace, user=user, is_active=True)
            # A'zolik roli 'STAFF' bo'lsa, ruxsat beramiz
            return member.role == 'STAFF'
        except WorkspaceMember.DoesNotExist:
            # Agar foydalanuvchi bu workspace'ning a'zosi bo'lmasa, ruxsat yo'q
            return False
