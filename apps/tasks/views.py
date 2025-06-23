# apps/tasks/views.py

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.shortcuts import get_object_or_404
from .models import Task, TaskComment
from .serializers import (
    TaskDetailSerializer, TaskCreateSerializer, TaskUpdateByTeamLeaderSerializer,
    TaskUpdateByAssigneeSerializer, TaskCommentSerializer, TaskCommentCreateSerializer
)
from .permissions import (
    IsWorkspaceMember, IsTeamLeaderForAction, IsAssigneeForStatusUpdate, IsCommentOwner
)

@extend_schema_view(
    create=extend_schema(summary="📋 Yangi vazifa yaratish (Faqat TeamLeader)", tags=['Tasks']),
    list=extend_schema(summary="📋 Ish maydonidagi vazifalar ro'yxati", tags=['Tasks']),
    retrieve=extend_schema(summary="📋 Vazifa ma'lumotlarini olish", tags=['Tasks']),
    update=extend_schema(summary="📋 Vazifani to'liq yangilash", tags=['Tasks']),
    partial_update=extend_schema(summary="📋 Vazifani qisman yangilash", tags=['Tasks']),
    destroy=extend_schema(summary="📋 Vazifani o'chirish (Faqat TeamLeader)", tags=['Tasks']),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('workspace', 'assigned_to', 'created_by').all()

    def get_serializer_class(self):
        # Schema generatsiyasi uchun xavfsiz serializer
        if getattr(self, 'swagger_fake_view', False):
            return TaskDetailSerializer
            
        if self.action == 'create':
            return TaskCreateSerializer
        
        if self.action in ['update', 'partial_update']:
            task = self.get_object()
            user = self.request.user
            # Agar so'rov yuborayotgan odam vazifani yaratgan Team Leader bo'lsa
            if task.created_by == user:
                return TaskUpdateByTeamLeaderSerializer
            # Agar so'rov yuborayotgan odam vazifaga biriktirilgan bo'lsa
            if task.assigned_to == user:
                return TaskUpdateByAssigneeSerializer
        
        # Barcha qolgan holatlar uchun (GET, yoki ruxsati bo'lmaganlar uchun)
        return TaskDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
            
        # Global admin barcha vazifalarni ko'radi
        if user.user_type == 'ADMIN':
            return self.queryset.all()
            
        # Foydalanuvchi a'zo bo'lgan barcha ish maydonlaridagi vazifalarni qaytaramiz
        user_workspace_ids = user.workspace_memberships.filter(is_active=True).values_list('workspace_id', flat=True)
        return self.queryset.filter(workspace_id__in=user_workspace_ids)

    def get_permissions(self):
        """Amalga qarab ruxsatnomalarni belgilash."""
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, IsTeamLeaderForAction]
        elif self.action in ['update', 'partial_update']:
            # Yoki vazifani yaratgan Team Leader, yoki vazifa berilgan shaxs o'zgartira oladi
            self.permission_classes = [permissions.IsAuthenticated, (IsTeamLeaderForAction | IsAssigneeForStatusUpdate)]
        elif self.action == 'destroy':
            # Faqat vazifani yaratgan Team Leader o'chira oladi
            self.permission_classes = [permissions.IsAuthenticated, IsTeamLeaderForAction]
        else: # list, retrieve
            # Ish maydoni a'zosi bo'lishi kifoya
            self.permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
        return super().get_permissions()

@extend_schema_view(
    create=extend_schema(summary="💬 Vazifaga izoh qo'shish", tags=['Task Comments']),
    list=extend_schema(summary="💬 Vazifa izohlari ro'yxati", tags=['Task Comments']),
    retrieve=extend_schema(summary="💬 Izoh ma'lumotlarini olish", tags=['Task Comments']),
    update=extend_schema(summary="💬 Izohni tahrirlash", tags=['Task Comments']),
    partial_update=extend_schema(summary="💬 Izohni qisman tahrirlash", tags=['Task Comments']),
    destroy=extend_schema(summary="💬 Izohni o'chirish", tags=['Task Comments']),
)
class TaskCommentViewSet(viewsets.ModelViewSet):
    queryset = TaskComment.objects.select_related('user').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCommentCreateSerializer
        return TaskCommentSerializer

    def get_queryset(self):
        return self.queryset.filter(task_id=self.kwargs.get('task_pk'))

    def get_permissions(self):
        # Schema generatsiyasi uchun
        if getattr(self, 'swagger_fake_view', False) or 'task_pk' not in self.kwargs:
            return [permission() for permission in self.permission_classes]

        # Asosiy tekshiruv
        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        if not IsWorkspaceMember().has_object_permission(self.request, self, task):
            self.permission_denied(self.request, message="Siz bu vazifaga izoh yoza olmaysiz yoki izohlarni ko'ra olmaysiz.")

        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsCommentOwner]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_pk'))
        serializer.save(user=self.request.user, task=task)     