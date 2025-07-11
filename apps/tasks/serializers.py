# apps/tasks/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Task, TaskComment
from apps.users.models import User
from apps.workspaces.models import Workspace, WorkspaceMember

from apps.users.serializers import UserSummarySerializer
from apps.workspaces.serializers import WorkspaceSummarySerializer
from apps.notifications.utils import create_notification

class TaskCommentSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    class Meta:
        model = TaskComment
        fields = ['id', 'user', 'comment', 'created_at']

class TaskCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ['comment']

class TaskListSerializer(serializers.ModelSerializer):
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'workspace', 'assigned_to', 'created_by', 
            'status', 'status_display', 'priority', 'priority_display', 'due_date'
        ]

class TaskDetailSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSummarySerializer(read_only=True)
    assigned_to = UserSummarySerializer(read_only=True)
    created_by = UserSummarySerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'

class TaskCreateSerializer(serializers.ModelSerializer):
    workspace = serializers.PrimaryKeyRelatedField(queryset=Workspace.objects.all(), label="Ish maydoni")
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), label="Bajaruvchi")
    
    class Meta:
        model = Task
        fields = ['workspace', 'title', 'description', 'assigned_to', 'priority', 'due_date']
    
    def validate(self, data):
        workspace = data.get('workspace')
        assignee = data.get('assigned_to')
        creator = self.context['request'].user
        try:
            assignee_membership = WorkspaceMember.objects.get(workspace=workspace, user=assignee)
            if assignee_membership.role not in ['STUDENT', 'TEAMLEADER']: 
                 raise serializers.ValidationError({"assigned_to": "Only students and team leaders can be assigned tasks."})
        except WorkspaceMember.DoesNotExist:
            raise serializers.ValidationError({"assigned_to": "The user being assigned is not a member of this workspace."})
        if creator == assignee:
            raise serializers.ValidationError({"assigned_to": "You cannot assign tasks to yourself."})
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskUpdateByTeamLeaderSerializer(serializers.ModelSerializer):
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
                verb=f"Task status changed",
                message=f"Task '{instance.title}' status changed from '{instance.get_status_display()}' to '{dict(Task.STATUS_CHOICES).get(new_status)}'.",
                action_object=instance
            )
        if new_status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        elif new_status != 'COMPLETED' and instance.completed_at is not None:
            instance.completed_at = None
        return super().update(instance, validated_data)


class TaskUpdateByAssigneeSerializer(serializers.ModelSerializer):
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
                verb=f"Task status updated",
                message=f"Task '{instance.title}' status changed from '{dict(Task.STATUS_CHOICES).get(old_status)}' to '{dict(Task.STATUS_CHOICES).get(new_status)}'.",
                action_object=instance
            )
        if new_status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        else:
            instance.completed_at = None
        return super().update(instance, validated_data)