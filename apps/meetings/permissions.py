# apps/meetings/permissions.py
from rest_framework import permissions
from .models import MeetingAttendee

class IsMeetingOrganizerOrAdmin(permissions.BasePermission):
    """Uchrashuvni faqat tashkilotchisi yoki Admin o'zgartira/o'chira oladi."""
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'ADMIN':
            return True
        return obj.organizer == request.user

class CanViewMeeting(permissions.BasePermission):
    """Uchrashuvni faqat a'zolari yoki taklif qilinganlar ko'ra oladi."""
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'ADMIN':
            return True
        # Agar uchrashuvga taklif qilingan bo'lsa
        is_attendee = MeetingAttendee.objects.filter(meeting=obj, user=request.user).exists()
        # Yoki workspace a'zosi bo'lsa (agar workspace'ga bog'langan bo'lsa)
        is_workspace_member = obj.workspace and obj.workspace.members.filter(user=request.user).exists()
        return is_attendee or is_workspace_member

class IsAttendee(permissions.BasePermission):
    """Faqat uchrashuvga taklif qilingan shaxs o'zining statusini o'zgartira oladi."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
