# apps/tasks/views.py

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.shortcuts import get_object_or_404

from apps.reports.models import MonthlyReport
from apps.notifications.utils import create_notification
from .models import Task, TaskComment
from .serializers import (
    TaskListSerializer, TaskDetailSerializer, 
    TaskCreateSerializer, TaskUpdateByTeamLeaderSerializer,
    TaskUpdateByAssigneeSerializer, TaskCommentSerializer, TaskCommentCreateSerializer
)
from .permissions import (
    IsWorkspaceMember, IsTeamLeaderForAction, IsAssigneeForStatusUpdate, IsCommentOwner
)

@extend_schema_view(
    create=extend_schema(summary="📋 Create New Task", tags=['Tasks']),
    list=extend_schema(summary="📋 List Tasks in Workspace", tags=['Tasks']),
    retrieve=extend_schema(summary="📋 Get Task Details", tags=['Tasks']),
    update=extend_schema(summary="📋 Update Task", tags=['Tasks']),
    partial_update=extend_schema(summary="📋 Partially Update Task", tags=['Tasks']),
    destroy=extend_schema(summary="📋 Delete Task (TeamLeader Only)", tags=['Tasks']),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('workspace', 'assigned_to', 'created_by').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return TaskDetailSerializer
            
        if self.action == 'list':
            return TaskListSerializer
                
        if self.action == 'create':
            return TaskCreateSerializer
        
        if self.action in ['update', 'partial_update']:
            task = self.get_object()
            user = self.request.user
            if task.created_by == user:
                return TaskUpdateByTeamLeaderSerializer
            if task.assigned_to == user:
                return TaskUpdateByAssigneeSerializer
        return TaskDetailSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
            
        if user.user_type == 'ADMIN':
            return self.queryset.all()
            
        user_workspace_ids = user.workspace_memberships.filter(is_active=True).values_list('workspace_id', flat=True)
        return self.queryset.filter(workspace_id__in=user_workspace_ids)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, IsTeamLeaderForAction]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [permissions.IsAuthenticated, (IsTeamLeaderForAction | IsAssigneeForStatusUpdate)]
        elif self.action == 'destroy':
            self.permission_classes = [permissions.IsAuthenticated, IsTeamLeaderForAction]
        else:
            self.permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
        return super().get_permissions()

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user)
        create_notification(
            recipient=task.assigned_to,
            actor=task.created_by,
            verb="assigned you a new task",
            message=f"'{task.created_by.get_full_name()}' assigned you a new task: '{task.title}'.",
            action_object=task
        )




@extend_schema_view(
    create=extend_schema(summary="💬 Add Comment to Task", tags=['Task Comments']),
    list=extend_schema(summary="💬 List Task Comments", tags=['Task Comments']),
    retrieve=extend_schema(summary="💬 Get Comment Details", tags=['Task Comments']),
    update=extend_schema(summary="💬 Update Comment", tags=['Task Comments']),
    partial_update=extend_schema(summary="💬 Partially Update Comment", tags=['Task Comments']),
    destroy=extend_schema(summary="💬 Delete Comment", tags=['Task Comments']),
)
class TaskCommentViewSet(viewsets.ModelViewSet):
    queryset = TaskComment.objects.select_related('user').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCommentCreateSerializer
        return TaskCommentSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TaskComment.objects.none()
        return self.queryset.filter(task_id=self.kwargs.get('task_pk'))

    def get_permissions(self):
        if getattr(self, 'swagger_fake_view', False) or 'task_pk' not in self.kwargs:
            return [permission() for permission in self.permission_classes]

        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        if not IsWorkspaceMember().has_object_permission(self.request, self, task):
            self.permission_denied(self.request, message="You must be a member of the workspace to comment on this task.")

        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsCommentOwner]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_pk'))
        commenter = self.request.user
        comment = serializer.save(user=commenter, task=task)
        
        create_notification(
            recipient=task.created_by,
            actor=commenter,
            verb="commented on your task",
            message=f"'{commenter.get_full_name()}' commented on your task: '{task.title}'.",
            action_object=comment
        )

        create_notification(
            recipient=task.assigned_to,
            actor=commenter,
            verb="commented on your task",
            message=f"'{commenter.get_full_name()}' commented on your task: '{task.title}'.",
            action_object=comment
        )