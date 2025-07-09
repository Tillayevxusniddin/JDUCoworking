# apps/tasks/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Task, TaskComment
from apps.users.models import User
from apps.workspaces.models import Workspace, WorkspaceMember

# ✅ YORDAMCHI OPTIMALLASHTIRILGAN SERIALIZER'LARNI IMPORT QILAMIZ
from apps.users.serializers import UserSummarySerializer
from apps.workspaces.serializers import WorkspaceSummarySerializer
from apps.notifications.utils import create_notification


# ----------------- TaskComment Serializers (qisman optimallashtirildi) -----------------

class TaskCommentSerializer(serializers.ModelSerializer):
    # ✅ Foydalanuvchi haqida qisqa ma'lumot qaytaramiz
    user = UserSummarySerializer(read_only=True)
    class Meta:
        model = TaskComment
        fields = ['id', 'user', 'comment', 'created_at']

class TaskCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ['comment']


# ----------------- Task Serializers (List va Detail'ga ajratilgan) -----------------

class TaskListSerializer(serializers.ModelSerializer):
    """Vazifalar ro'yxati uchun optimallashtirilgan serializer."""
    # ✅ Barcha bog'liq modellar endi faqat ID qaytaradi
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # Qo'shimcha qulaylik uchun "display" maydonlari
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'workspace', 'assigned_to', 'created_by', 
            'status', 'status_display', 'priority', 'priority_display', 'due_date'
        ]

class TaskDetailSerializer(serializers.ModelSerializer):
    """Bitta vazifa uchun to'liq ma'lumot beruvchi serializer."""
    # ✅ Bog'liq modellar endi SummarySerializer'lar orqali qisqa ma'lumot qaytaradi
    workspace = WorkspaceSummarySerializer(read_only=True)
    assigned_to = UserSummarySerializer(read_only=True)
    created_by = UserSummarySerializer(read_only=True)
    
    comments = TaskCommentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'


# ----------------- Create / Update Serializers (o'zgarishsiz, lekin bildirishnoma mantiqi bilan) -----------------

class TaskCreateSerializer(serializers.ModelSerializer):
    """TeamLeader tomonidan vazifa yaratish uchun serializer."""
    workspace = serializers.PrimaryKeyRelatedField(queryset=Workspace.objects.all(), label="Ish maydoni")
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), label="Bajaruvchi")
    
    class Meta:
        model = Task
        fields = ['workspace', 'title', 'description', 'assigned_to', 'priority', 'due_date']
    
    # ... `validate` va `create` metodlari o'zgarishsiz qoladi ...
    def validate(self, data):
        workspace = data.get('workspace')
        assignee = data.get('assigned_to')
        creator = self.context['request'].user
        try:
            assignee_membership = WorkspaceMember.objects.get(workspace=workspace, user=assignee)
            if assignee_membership.role not in ['STUDENT', 'TEAMLEADER']: # TeamLeader ham vazifa olishi mumkin
                 raise serializers.ValidationError({"assigned_to": "Vazifani faqat 'STUDENT' yoki 'TEAMLEADER' rolidagi a'zolarga biriktirish mumkin."})
        except WorkspaceMember.DoesNotExist:
            raise serializers.ValidationError({"assigned_to": "Vazifa berilayotgan foydalanuvchi bu ish maydonining a'zosi emas."})
        if creator == assignee:
            raise serializers.ValidationError({"assigned_to": "O'zingizga vazifa biriktira olmaysiz."})
        return data

    def create(self, validated_data):
        # Bu metod endi `perform_create`ga ko'chirilgani uchun bo'sh qolishi mumkin,
        # lekin `created_by`ni qo'shib qo'yish xavfsizroq.
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskUpdateByTeamLeaderSerializer(serializers.ModelSerializer):
    """TeamLeader tomonidan vazifani tahrirlash uchun."""
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date', 'status']
    
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        if new_status != old_status:
            create_notification(
                recipient=instance.assigned_to,
                actor=self.context['request'].user,
                verb=f"vazifa statusini o'zgartirdi",
                message=f"'{instance.title}' nomli vazifaning statusi '{instance.get_status_display()}'dan '{dict(Task.STATUS_CHOICES).get(new_status)}'ga o'zgartirildi.",
                action_object=instance
            )
        if new_status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        elif new_status != 'COMPLETED' and instance.completed_at is not None:
            instance.completed_at = None
        return super().update(instance, validated_data)


class TaskUpdateByAssigneeSerializer(serializers.ModelSerializer):
    """Bajaruvchi tomonidan statusni o'zgartirish uchun."""
    status = serializers.ChoiceField(choices=[('INPROGRESS', 'InProgress'), ('COMPLETED', 'Completed')])
    class Meta:
        model = Task
        fields = ['status']
    
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        if new_status != old_status:
            create_notification(
                recipient=instance.created_by,
                actor=self.context['request'].user,
                verb=f"vazifa statusini o'zgartirdi",
                message=f"'{instance.assigned_to.get_full_name()}' siz yaratgan '{instance.title}' vazifasining statusini '{dict(Task.STATUS_CHOICES).get(new_status)}'ga o'zgartirdi.",
                action_object=instance
            )
        if new_status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        else:
            instance.completed_at = None
        return super().update(instance, validated_data)