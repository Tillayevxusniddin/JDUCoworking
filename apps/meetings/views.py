# apps/meetings/views.py

from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import models, transaction
from drf_spectacular.utils import extend_schema

from .models import Meeting, MeetingAttendee
from .serializers import (
    MeetingListSerializer, MeetingDetailSerializer, MeetingCreateSerializer, 
    MeetingAttendeeListSerializer, MeetingAttendeeDetailSerializer, 
    AttendeeStatusUpdateSerializer, MeetingLinkUpdateSerializer
)
from .permissions import IsMeetingOrganizerOrAdmin, IsAttendee
from apps.users.permissions import IsAdminOrStaff
from apps.users.models import User
from .google_api import create_google_meet_event
from apps.notifications.utils import create_notification


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all().prefetch_related('attendees__user', 'workspace', 'organizer')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MeetingListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return MeetingCreateSerializer
        if self.action == 'set_meet_link':
            return MeetingLinkUpdateSerializer
        return MeetingDetailSerializer 
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'set_meet_link']:
            self.permission_classes = [IsMeetingOrganizerOrAdmin]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [IsAdminOrStaff]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'ADMIN':
            return self.queryset
        
        user_workspaces = user.workspace_memberships.values_list('workspace_id', flat=True)
        user_meetings = user.meeting_attendances.values_list('meeting_id', flat=True)
        
        return self.queryset.filter(
            models.Q(workspace_id__in=user_workspaces) | models.Q(id__in=user_meetings)
        ).distinct()

    def perform_create(self, serializer):
        meeting = serializer.save(organizer=self.request.user)
        invited_users_data = serializer.validated_data.get('invited_users', [])
        attendee_users_qs = User.objects.none()

        if meeting.audience_type == Meeting.AudienceType.WORKSPACE_MEMBERS and meeting.workspace:
            attendee_users_qs = User.objects.filter(workspace_memberships__workspace=meeting.workspace, is_active=True)
        elif meeting.audience_type == Meeting.AudienceType.ALL_STAFF:
            attendee_users_qs = User.objects.filter(user_type__in=['STAFF', 'ADMIN'], is_active=True)
        elif meeting.audience_type == Meeting.AudienceType.SPECIFIC_USERS:
            attendee_users_qs = User.objects.filter(id__in=[user.id for user in invited_users_data])

        attendees_emails = set(attendee_users_qs.values_list('email', flat=True))
        if meeting.organizer and meeting.organizer.email:
            attendees_emails.add(meeting.organizer.email)
        
        final_attendee_emails = list(attendees_emails)

        with transaction.atomic():
            attendee_users = User.objects.filter(email__in=final_attendee_emails)
            attendees_to_create = [MeetingAttendee(meeting=meeting, user=user) for user in attendee_users]
            if attendees_to_create:
                MeetingAttendee.objects.bulk_create(attendees_to_create, ignore_conflicts=True)

        if not meeting.google_event_id and final_attendee_emails:
            link, event_id = create_google_meet_event(
                meeting.title, meeting.description, meeting.start_time,
                meeting.end_time, final_attendee_emails
            )
            if link and event_id:
                meeting.meeting_link = link
                meeting.google_event_id = event_id
                meeting.save(update_fields=['meeting_link', 'google_event_id'])

        for attendee in meeting.attendees.all():
            create_notification(
                recipient=attendee.user,
                actor=meeting.organizer,
                verb="You have been invited to a meeting",
                message=f"You have been invited to a new meeting titled '{meeting.title}'.",
                action_object=meeting
            )

    @extend_schema(
        summary="[Organizer/ADMIN] Set Google Meet Link",
        request=MeetingLinkUpdateSerializer,
        responses={200: MeetingDetailSerializer}
    )
    @action(detail=True, methods=['patch'], url_path='set-link')
    def set_meet_link(self, request, pk=None):
        """
        Set or update the Google Meet link for a meeting.
        """
        meeting = self.get_object()
        self.check_object_permissions(request, meeting) 

        serializer = self.get_serializer(instance=meeting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(MeetingDetailSerializer(meeting).data)

class MeetingAttendeeViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    queryset = MeetingAttendee.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return MeetingAttendeeListSerializer
        if self.action in ['update', 'partial_update']:
            return AttendeeStatusUpdateSerializer
        return MeetingAttendeeDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['ADMIN', 'STAFF']:
            return MeetingAttendee.objects.all().select_related('user', 'meeting')
        return MeetingAttendee.objects.filter(user=user).select_related('user', 'meeting')
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAttendee]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        attendee = serializer.save(responded_at=timezone.now())
        new_status = attendee.status
        
        if new_status != old_status:
            meeting = attendee.meeting
            organizer = meeting.organizer
            responder = attendee.user
            
            if organizer != responder:
                status_text = "accepted" if new_status == 'ACCEPTED' else "declined"

                create_notification(
                    recipient=organizer,
                    actor=responder,
                    verb=f"You have {status_text} the meeting invitation",
                    message=f"'{responder.get_full_name()}' has {status_text} the invitation to the meeting titled '{meeting.title}'.",
                    action_object=meeting
                )
