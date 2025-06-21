# apps/tasks/permissions.py

from rest_framework import permissions
from apps.workspaces.models import WorkspaceMember

class CanViewTask(permissions.BasePermission):
    """
    Foydalanuvchi vazifani ko'ra olishini tekshiradi.
    Faqat vazifa tegishli bo'lgan ish maydoni a'zolari ko'ra oladi.
    """
    message = "Sizda bu vazifani ko'rish huquqi yo'q."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.user_type in ['ADMIN', 'STAFF']:
            return True
        return WorkspaceMember.objects.filter(workspace=obj.workspace, user=user, is_active=True).exists()

class CanModifyTask(permissions.BasePermission):
    """
    Vazifani o'zgartirish yoki o'chirish huquqini tekshiradi.
    Faqat ADMIN yoki vazifani yaratgan MODERATOR/ADMIN rolidagi shaxs o'zgartira oladi.
    """
    message = "Sizda bu vazifani o'zgartirish yoki o'chirish huquqi yo'q."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.user_type == 'ADMIN':
            return True
        try:
            membership = WorkspaceMember.objects.get(workspace=obj.workspace, user=user)
            return obj.created_by == user and membership.role in ['ADMIN', 'MODERATOR']
        except WorkspaceMember.DoesNotExist:
            return False

class IsAssigneeForStatusUpdate(permissions.BasePermission):
    """Foydalanuvchi vazifani bajaruvchisi ekanligini tekshiradi (faqat status uchun)."""
    message = "Faqat vazifaga tayinlangan shaxs uning statusini o'zgartira oladi."

    def has_object_permission(self, request, view, obj):
        return obj.assigned_to == request.user

class IsCommentOwner(permissions.BasePermission):
    """Foydalanuvchi izoh egasi ekanligini tekshiradi."""
    message = "Faqat izoh egasi uni o'zgartira yoki o'chira oladi."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user