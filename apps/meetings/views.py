# apps/meetings/views.py
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Meeting, MeetingAttendee
from .serializers import MeetingSerializer, MeetingCreateSerializer, MeetingAttendeeSerializer, AttendeeStatusUpdateSerializer, MeetingLinkUpdateSerializer
from .permissions import IsMeetingOrganizerOrAdmin, CanViewMeeting, IsAttendee
from apps.users.permissions import IsAdminOrStaff
from django.db import models
from drf_spectacular.utils import extend_schema, OpenApiParameter



class MeetingViewSet(viewsets.ModelViewSet):
    """Uchrashuvlarni boshqarish uchun."""
    queryset = Meeting.objects.all().prefetch_related('attendees__user')
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return MeetingCreateSerializer
        return MeetingSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsMeetingOrganizerOrAdmin]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated] # Keyinroq obyekt darajasida tekshiriladi
        else: # create
            self.permission_classes = [IsAdminOrStaff]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'ADMIN':
            return self.queryset
        # Foydalanuvchi a'zo bo'lgan workspace'lardagi yoki o'zi taklif qilingan uchrashuvlar
        user_workspaces = user.workspace_memberships.values_list('workspace_id', flat=True)
        user_meetings = user.meeting_attendances.values_list('meeting_id', flat=True)
        return self.queryset.filter(
            models.Q(workspace_id__in=user_workspaces) | models.Q(id__in=user_meetings)
        ).distinct()

class MeetingAttendeeViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Uchrashuv qatnashchilari o'zlarining statusini yangilashi uchun."""
    queryset = MeetingAttendee.objects.all()
    serializer_class = AttendeeStatusUpdateSerializer
    permission_classes = [IsAttendee]

    def perform_update(self, serializer):
        serializer.save(responded_at=timezone.now())

    @extend_schema(
        summary="[Organizer/ADMIN] Uchrashuvga Google Meet havolasini qo'shish",
        request=MeetingLinkUpdateSerializer,
        tags=['Uchrashuvlar']
    )
    @action(detail=True, methods=['patch'], url_path='set-link')
    def set_meet_link(self, request, pk=None):
        """
        Mavjud uchrashuvga Google Meet havolasini qo'shish/yangilash.
        Faqat uchrashuv tashkilotchisi yoki Admin bajara oladi.
        """
        meeting = self.get_object()
        # Ruxsatni tekshirish (faqat tashkilotchi yoki Admin)
        self.check_object_permissions(request, meeting)

        serializer = MeetingLinkUpdateSerializer(instance=meeting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MeetingSerializer(meeting).data)
