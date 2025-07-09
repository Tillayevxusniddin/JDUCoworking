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
        summary="🔔 Mening bildirishnomalarim ro'yxati",
        responses=NotificationListSerializer(many=True) # Javob qanday bo'lishini ko'rsatamiz
    ),
    retrieve=extend_schema(
        summary="🔔 Bitta bildirishnomani ko'rish",
        responses=NotificationDetailSerializer # Javob qanday bo'lishini ko'rsatamiz
    ),
    mark_as_read=extend_schema(summary="✔️ Bildirishnomani 'o'qilgan' deb belgilash"),
    mark_all_as_read=extend_schema(summary="✔️ Barcha bildirishnomalarni 'o'qilgan' deb belgilash"),
    unread_count=extend_schema(summary="🔢 O'qilmagan bildirishnomalar soni")
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
        """Bitta bildirishnomani o'qilgan deb belgilaydi."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Barcha o'qilmagan bildirishnomalarni o'qilgan deb belgilaydi."""
        unread_notifications = self.get_queryset().filter(is_read=False)
        count = unread_notifications.count()
        unread_notifications.update(is_read=True)
        return Response({'status': f'{count} notifications marked as read'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """O'qilmagan bildirishnomalar sonini qaytaradi."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)