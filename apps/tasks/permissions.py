from rest_framework import permissions
from apps.users.models import Student

class IsTeamLeadUser(permissions.BasePermission):
    """Foydalanuvchi 'STUDENT' va 'TEAMLEAD' statusida ekanligini tekshiradi."""
    message = "Bu amal uchun faqat Jamoa Liderlari (TeamLead) huquqiga ega."

    def has_permission(self, request, view):
        user = request.user
        if not (user.is_authenticated and user.user_type == 'STUDENT'):
            return False
        try:
            return user.student_profile.level_status == 'TEAMLEAD'
        except Student.DoesNotExist:
            return False

class CanViewTask(permissions.BasePermission):
    """
    Foydalanuvchi vazifani ko'ra olishini tekshiradi (obyekt darajasida).
    ADMIN, STAFF, TEAMLEAD, vazifa yaratuvchisi yoki bajaruvchisi ko'ra oladi.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        
        is_teamlead = (user.user_type == 'STUDENT' and getattr(user.student_profile, 'level_status', 'SIMPLE') == 'TEAMLEAD')

        if user.user_type in ['ADMIN', 'STAFF'] or is_teamlead:
            return True
            
        return obj.created_by == user or obj.assigned_to == user

class IsTaskCreatorForUpdate(permissions.BasePermission):
    """Foydalanuvchi vazifani yaratgan TeamLead ekanligini tekshiradi."""
    message = "Faqat vazifani yaratgan Jamoa Lideri uni to'liq o'zgartira oladi."
    
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user and IsTeamLeadUser().has_permission(request, view)

class IsAssigneeForStatusUpdate(permissions.BasePermission):
    """Foydalanuvchi vazifani bajaruvchisi ekanligini tekshiradi."""
    message = "Faqat vazifaga tayinlangan shaxs uning statusini o'zgartira oladi."

    def has_object_permission(self, request, view, obj):
        return obj.assigned_to == request.user

class IsCommentOwner(permissions.BasePermission):
    """Foydalanuvchi izoh egasi ekanligini tekshiradi."""
    message = "Faqat izoh egasi uni o'zgartira yoki o'chira oladi."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user