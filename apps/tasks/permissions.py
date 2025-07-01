# apps/tasks/permissions.py

from rest_framework import permissions
from apps.workspaces.models import WorkspaceMember

def get_user_role_in_workspace(user, workspace):
    """Yordamchi funksiya: Foydalanuvchining workspace'dagi rolini qaytaradi."""
    try:
        return WorkspaceMember.objects.get(workspace=workspace, user=user).role
    except WorkspaceMember.DoesNotExist:
        return None

class IsWorkspaceMember(permissions.BasePermission):
    """Foydalanuvchi vazifa tegishli bo'lgan ish maydonining a'zosi ekanligini tekshiradi."""
    message = "Siz bu ish maydonining a'zosi emassiz."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.user_type == 'ADMIN': # Global Admin hamma narsani ko'ra oladi
            return True
        # `obj` bu Task instansi
        return WorkspaceMember.objects.filter(workspace=obj.workspace, user=user, is_active=True).exists()

# apps/tasks/permissions.py

class IsTeamLeaderForAction(permissions.BasePermission):
    """
    Vazifa yaratish, o'zgartirish yoki o'chirish uchun foydalanuvchi TEAMLEADER ekanligini tekshiradi.
    """
    message = "Bu amalni faqat ish maydonidagi Jamoa Lideri (Team Leader) yoki vazifa yaratuvchisi bajara oladi."

    def has_permission(self, request, view):
        """
        Umumiy ruxsatni tekshirish. Asosan 'create' uchun ishlaydi.
        Boshqa amallar uchun tekshiruvni has_object_permission'ga o'tkazadi.
        """
        user = request.user
        if not user.is_authenticated:
            return False

        # Agar amal 'create' bo'lsa, workspace'dagi rolini tekshiramiz
        if view.action == 'create':
            # 'create' uchun workspace_id so'rov tanasida kelishi kerak
            workspace_id = request.data.get('workspace')
            if not workspace_id:
                # Agar create so'rovida workspace ko'rsatilmagan bo'lsa, xatolik
                self.message = "Vazifa yaratish uchun 'workspace' ID'si ko'rsatilishi shart."
                return False
            
            role = get_user_role_in_workspace(user, workspace_id)
            return role == 'TEAMLEADER'

        # 'update', 'destroy', 'retrieve' kabi boshqa amallar uchun
        # tekshiruvni keyingi bosqichga (has_object_permission) o'tkazamiz.
        return True

    def has_object_permission(self, request, view, obj):
        """Obyekt darajasidagi ruxsatni tekshirish (update, destroy uchun)."""
        user = request.user
        role = get_user_role_in_workspace(user, obj.workspace)
        
        # Faqat vazifani yaratgan team leader o'zgartira oladi yoki o'chira oladi
        return obj.created_by == user and role == 'TEAMLEADER'

class IsAssigneeForStatusUpdate(permissions.BasePermission):
    """Faqat vazifa biriktirilgan shaxs statusni o'zgartira olishini tekshiradi."""
    message = "Faqat vazifaga biriktirilgan shaxs uning statusini o'zgartira oladi."

    def has_object_permission(self, request, view, obj):
        return obj.assigned_to == request.user

class IsCommentOwner(permissions.BasePermission):
    """Foydalanuvchi izoh egasi ekanligini tekshiradi."""
    message = "Faqat izoh egasi uni o'zgartira yoki o'chira oladi."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user