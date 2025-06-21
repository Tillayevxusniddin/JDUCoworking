# apps/tasks/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.db.models import Q
# --- XATOLIKNI TO'G'IRLASH UCHUN QO'SHILGAN IMPORT ---
from drf_spectacular.utils import extend_schema, extend_schema_view
# ----------------------------------------------------
from django.shortcuts import get_object_or_404
from .models import Task, TaskComment
from .serializers import (
    TaskDetailSerializer, TaskCreateUpdateSerializer, TaskUpdateByAssigneeSerializer,
    TaskCommentSerializer, TaskCommentCreateSerializer
)
from .permissions import (
    CanViewTask, CanModifyTask, IsAssigneeForStatusUpdate, IsCommentOwner
)

@extend_schema_view(
    create=extend_schema(summary="📋 Yangi vazifa yaratish (Ish maydoni moderatori/admini)", tags=['Tasks']),
    list=extend_schema(summary="📋 Sizga tegishli vazifalar ro'yxati", tags=['Tasks']),
    retrieve=extend_schema(summary="📋 Vazifa ma'lumotlarini olish", tags=['Tasks']),
    update=extend_schema(summary="📋 Vazifani to'liq yangilash", tags=['Tasks']),
    partial_update=extend_schema(summary="📋 Vazifani qisman yangilash", tags=['Tasks']),
    destroy=extend_schema(summary="📋 Vazifani o'chirish", tags=['Tasks']),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('workspace', 'assigned_to', 'created_by').prefetch_related('comments__user').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateUpdateSerializer
        
        if self.action in ['update', 'partial_update']:
            task = self.get_object()
            if CanModifyTask().has_object_permission(self.request, self, task):
                return TaskCreateUpdateSerializer 
            if IsAssigneeForStatusUpdate().has_object_permission(self.request, self, task):
                return TaskUpdateByAssigneeSerializer
        
        return TaskDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        if user.user_type in ['ADMIN', 'STAFF']:
            return self.queryset.all()
        
        user_workspace_ids = user.workspace_memberships.filter(is_active=True).values_list('workspace_id', flat=True)
        return self.queryset.filter(workspace_id__in=user_workspace_ids)

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            self.permission_classes = [permissions.IsAuthenticated, (CanModifyTask | IsAssigneeForStatusUpdate)]
        elif self.action == 'destroy':
            self.permission_classes = [permissions.IsAuthenticated, CanModifyTask]
        elif self.action == 'retrieve':
            self.permission_classes = [permissions.IsAuthenticated, CanViewTask]
        else: # create, list
            self.permission_classes = [permissions.IsAuthenticated]
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
        if getattr(self, 'swagger_fake_view', False) or 'task_pk' not in self.kwargs:
            return [permission() for permission in self.permission_classes]

        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        if not CanViewTask().has_object_permission(self.request, self, task):
            self.permission_denied(self.request, message="Siz bu vazifaga izoh yoza olmaysiz yoki izohlarni ko'ra olmaysiz.")

        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsCommentOwner]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        serializer.save(user=self.request.user, task=task)