# apps/tasks/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Task, TaskComment
from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.workspaces.serializers import WorkspaceSerializer

# --- IZOH SERIALIZER'LARI (O'zgarishsiz) ---
class TaskCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ['comment']

class TaskCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = TaskComment
        fields = ['id', 'user', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

# --- VAZIFA SERIALIZER'LARI (YANGILANGAN) ---

# Vazifa yaratish va to'liq tahrirlash uchun
class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    workspace = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(),
        label="Ish maydoni"
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        label="Bajaruvchi"
    )

    class Meta:
        model = Task
        fields = [
            'id', 'workspace', 'title', 'description', 
            'assigned_to', 'priority', 'due_date', 'status'
        ]
        extra_kwargs = {
            'status': {'required': False} # `update` uchun ixtiyoriy
        }

    def validate(self, data):
        workspace = data.get('workspace')
        assigned_to_user = data.get('assigned_to')
        requesting_user = self.context['request'].user
        
        # O'zgartirish (update) vaqtida, agar workspace o'zgartirilmasa, instance'dan olamiz
        if self.instance and 'workspace' not in data:
            workspace = self.instance.workspace

        try:
            creator_membership = WorkspaceMember.objects.get(workspace=workspace, user=requesting_user)
        except WorkspaceMember.DoesNotExist:
            raise serializers.ValidationError({"workspace": "Siz bu ish maydonining a'zosi emassiz."})

        if creator_membership.role not in ['ADMIN', 'MODERATOR']:
            raise serializers.ValidationError({"detail": "Faqat ish maydoni admini yoki moderatori vazifa yarata/o'zgartira oladi."})

        if not WorkspaceMember.objects.filter(workspace=workspace, user=assigned_to_user).exists():
            raise serializers.ValidationError({"assigned_to": "Vazifa berilayotgan foydalanuvchi bu ish maydonining a'zosi emas."})
            
        if requesting_user == assigned_to_user:
            raise serializers.ValidationError({"assigned_to": "O'zingizga vazifa biriktira olmaysiz."})

        return data
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        status = validated_data.get('status', instance.status)
        if status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        elif status != 'COMPLETED' and instance.completed_at is not None:
            instance.completed_at = None
        return super().update(instance, validated_data)

# Bajaruvchi (Assignee) faqat statusni o'zgartirishi uchun
class TaskUpdateByAssigneeSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[
        ('INPROGRESS', 'InProgress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ])

    class Meta:
        model = Task
        fields = ['status']
    
    def update(self, instance, validated_data):
        status = validated_data.get('status')
        if status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        elif status != 'COMPLETED' and instance.completed_at is not None:
            instance.completed_at = None
        return super().update(instance, validated_data)

# Vazifani ko'rsatish uchun asosiy serializer
class TaskDetailSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'