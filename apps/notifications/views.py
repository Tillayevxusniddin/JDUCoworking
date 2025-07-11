# apps/notifications/views.py

from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Notification
from drf_spectacular.utils import extend_schema_view, OpenApiParameter, OpenApiResponse
from .serializers import NotificationListSerializer, NotificationDetailSerializer

@extend_schema_view(
    list=extend_schema(
        summary="🔔 My notifications list",
        responses=NotificationListSerializer(many=True) 
    ),
    retrieve=extend_schema(
        summary="🔔 View a single notification",
        responses=NotificationDetailSerializer
    ),
    mark_as_read=extend_schema(summary="✔️ Mark notification as read"),
    mark_all_as_read=extend_schema(summary="✔️ Mark all notifications as read"),
    unread_count=extend_schema(summary="🔢 Unread notifications count")
)
class NotificationViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    
    permission_classes = [permissions.IsAuthenticated]
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationDetailSerializer
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all unread notifications as read."""
        unread_notifications = self.get_queryset().filter(is_read=False)
        count = unread_notifications.count()
        unread_notifications.update(is_read=True)
        return Response({'status': f'{count} notifications marked as read'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get the count of unread notifications."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)