# apps/tasks/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Task, TaskComment
from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.workspaces.serializers import WorkspaceSerializer

# --- IZOH SERIALIZER'LARI (O'zgarishsiz qoladi) ---
class TaskCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ['comment']

class TaskCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = TaskComment
        fields = ['id', 'user', 'comment', 'created_at']

# --- VAZIFA SERIALIZER'LARI (YANGI MANTIQ ASOSIDA) ---

class TaskDetailSerializer(serializers.ModelSerializer):
    """Vazifani ko'rsatish uchun to'liq (read-only) serializer."""
    workspace = WorkspaceSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    class Meta:
        model = Task
        fields = '__all__'

class TaskCreateSerializer(serializers.ModelSerializer):
    """TeamLeader tomonidan vazifa yaratish uchun serializer."""
    workspace = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(),
        label="Ish maydoni"
    )
    # Vazifa beriladigan foydalanuvchi
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        label="Bajaruvchi"
    )
    class Meta:
        model = Task
        fields = ['workspace', 'title', 'description', 'assigned_to', 'priority', 'due_date']

    def validate(self, data):
        workspace = data.get('workspace')
        assignee = data.get('assigned_to')
        creator = self.context['request'].user

        # 1. Vazifa berilayotgan shaxs shu ish maydonida 'STUDENT' rolidami?
        try:
            assignee_membership = WorkspaceMember.objects.get(workspace=workspace, user=assignee)
            if assignee_membership.role != 'STUDENT':
                raise serializers.ValidationError({"assigned_to": "Vazifani faqat 'STUDENT' rolidagi a'zolarga biriktirish mumkin."})
        except WorkspaceMember.DoesNotExist:
            raise serializers.ValidationError({"assigned_to": "Vazifa berilayotgan foydalanuvchi bu ish maydonining a'zosi emas."})
            
        # 2. Bajaruvchi va yaratuvchi bir xil bo'la olmaydi
        if creator == assignee:
            raise serializers.ValidationError({"assigned_to": "O'zingizga vazifa biriktira olmaysiz."})

        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskUpdateByTeamLeaderSerializer(serializers.ModelSerializer):
    """TeamLeader tomonidan vazifani tahrirlash uchun (barcha statuslar mavjud)."""
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    class Meta:
        model = Task
        # TeamLeader hamma maydonni o'zgartira oladi
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date', 'status']
    
    def update(self, instance, validated_data):
        # completed_at mantiqini qo'shamiz
        status = validated_data.get('status', instance.status)
        if status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        elif status != 'COMPLETED' and instance.completed_at is not None:
            instance.completed_at = None
        return super().update(instance, validated_data)


class TaskUpdateByAssigneeSerializer(serializers.ModelSerializer):
    """Bajaruvchi tomonidan statusni o'zgartirish uchun."""
    status = serializers.ChoiceField(choices=[
        ('INPROGRESS', 'InProgress'),
        ('COMPLETED', 'Completed'),
    ])
    class Meta:
        model = Task
        fields = ['status']
    
    def update(self, instance, validated_data):
        status = validated_data.get('status')
        if status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        else:
            # Agar 'INPROGRESS'ga qaytarilsa, tugatilgan vaqtni olib tashlaymiz
            instance.completed_at = None
        return super().update(instance, validated_data)