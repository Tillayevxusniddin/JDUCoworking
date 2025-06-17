from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Task, TaskComment
from .serializers import (
    TaskSerializer, TaskCreateSerializer, TaskUpdateByTeamLeadSerializer,
    TaskUpdateByStudentSerializer, TaskCommentSerializer, TaskCommentCreateSerializer
)
from .permissions import (
    IsTeamLeadUser, CanViewTask, IsTaskCreatorForUpdate,
    IsAssigneeForStatusUpdate, IsCommentOwner
)
from django.shortcuts import get_object_or_404 # get_object_or_404 import qilamiz

# TaskViewSet o'zgarishsiz qoladi, u to'g'ri ishlayapti
@extend_schema_view(
    create=extend_schema(
        summary="📋 Yangi vazifa yaratish (Faqat TeamLead)",
        tags=['Tasks'],
        description="Faqat 'TEAMLEAD' statusidagi studentlar yangi vazifa yarata oladi."
    ),
    list=extend_schema(summary="📋 Barcha vazifalar ro'yxati", tags=['Tasks']),
    retrieve=extend_schema(summary="📋 Vazifa ma'lumotlarini olish", tags=['Tasks']),
    update=extend_schema(summary="📋 Vazifani to'liq yangilash (Faqat Yaratuvchi-TeamLead)", tags=['Tasks']),
    partial_update=extend_schema(summary="📋 Vazifani qisman yangilash", tags=['Tasks']),
    destroy=extend_schema(summary="📋 Vazifani o'chirish (Faqat Yaratuvchi-TeamLead)", tags=['Tasks']),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('assigned_to', 'created_by').prefetch_related('comments__user').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        
        if self.action in ['update', 'partial_update']:
            user = self.request.user
            task = self.get_object()
            if IsTaskCreatorForUpdate().has_object_permission(self.request, self, task):
                return TaskUpdateByTeamLeadSerializer
            if IsAssigneeForStatusUpdate().has_object_permission(self.request, self, task):
                return TaskUpdateByStudentSerializer
        
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()

        is_teamlead = (user.user_type == 'STUDENT' and getattr(user.student_profile, 'level_status', 'SIMPLE') == 'TEAMLEAD')
        if user.user_type in ['ADMIN', 'STAFF'] or is_teamlead:
            return super().get_queryset()

        return super().get_queryset().filter(assigned_to=user)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, IsTeamLeadUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()
    
    def perform_destroy(self, instance):
        if not (self.request.user.user_type == 'ADMIN' or IsTaskCreatorForUpdate().has_object_permission(self.request, self, instance)):
            self.permission_denied(self.request, message="Faqat Admin yoki vazifani yaratgan TeamLead o'chira oladi.")
        instance.delete()
        
    def perform_update(self, serializer):
        if not (IsTaskCreatorForUpdate().has_object_permission(self.request, self, serializer.instance) or IsAssigneeForStatusUpdate().has_object_permission(self.request, self, serializer.instance)):
            self.permission_denied(self.request, message="Sizda bu vazifani o'zgartirish huquqi yo'q.")
        serializer.save()


# TaskCommentViewSet'ga o'zgarish kiritamiz
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
        return super().get_queryset().filter(task_id=self.kwargs.get('task_pk'))

    def get_permissions(self):
        # ------ YECHIM SHU YERDA ------
        # Agar bu schema generatsiyasi bo'lsa yoki 'task_pk' mavjud bo'lmasa,
        # dinamik tekshiruvlarni o'tkazib yuboramiz.
        if getattr(self, 'swagger_fake_view', False) or 'task_pk' not in self.kwargs:
            return [permission() for permission in self.permission_classes]

        # Agar oddiy so'rov bo'lsa, mantiqni ishlatamiz
        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        if not CanViewTask().has_object_permission(self.request, self, task):
            self.permission_denied(self.request, message="Vazifani ko'ra olmaydiganlar izoh yozish yoki ko'rish huquqiga ega emas.")

        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsCommentOwner]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        serializer.save(user=self.request.user, task=task)