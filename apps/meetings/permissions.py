# apps/meetings/permissions.py
from rest_framework import permissions
from .models import MeetingAttendee

class IsMeetingOrganizerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'ADMIN':
            return True
        return obj.organizer == request.user

class CanViewMeeting(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'ADMIN':
            return True
        is_attendee = MeetingAttendee.objects.filter(meeting=obj, user=request.user).exists()
        is_workspace_member = obj.workspace and obj.workspace.members.filter(user=request.user).exists()
        return is_attendee or is_workspace_member

class IsAttendee(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
