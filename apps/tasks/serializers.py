from rest_framework import serializers
from django.utils import timezone
from .models import Task, TaskComment
from apps.users.models import User, Student
from apps.users.serializers import UserSerializer

class TaskCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'user', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    """Vazifalarni ko'rsatish uchun to'liq serializer."""
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'assigned_to', 'created_by', 
            'status', 'status_display', 'priority', 'priority_display', 'due_date', 
            'created_at', 'updated_at', 'completed_at', 'comments'
        ]

class TaskCreateSerializer(serializers.ModelSerializer):
    """TeamLead tomonidan vazifa yaratish uchun serializer."""
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='STUDENT', student_profile__level_status='SIMPLE'),
        write_only=True,
        label="Bajaruvchi (Simple Student)"
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to_id', 'priority', 'due_date']
    
    def create(self, validated_data):
        validated_data['assigned_to'] = validated_data.pop('assigned_to_id')
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class TaskUpdateByTeamLeadSerializer(serializers.ModelSerializer):
    """TeamLead tomonidan vazifani to'liq yangilash uchun."""
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='STUDENT', student_profile__level_status='SIMPLE'),
        write_only=True, required=False,
        label="Bajaruvchi (Simple Student)"
    )
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to_id', 'status', 'priority', 'due_date']

    def update(self, instance, validated_data):
        if 'assigned_to_id' in validated_data:
            instance.assigned_to = validated_data.pop('assigned_to_id')
        
        # `completed_at` mantiqini qo'shamiz
        status = validated_data.get('status', instance.status)
        if status == 'COMPLETED' and instance.status != 'COMPLETED':
            instance.completed_at = timezone.now()
        elif status != 'COMPLETED' and instance.status == 'COMPLETED':
            instance.completed_at = None
        
        return super().update(instance, validated_data)

class TaskUpdateByStudentSerializer(serializers.ModelSerializer):
    """SIMPLE student tomonidan vazifa statusini yangilash uchun."""
    status = serializers.ChoiceField(choices=[
        ('INPROGRESS', 'InProgress'),
        ('COMPLETED', 'Completed'),
    ])

    class Meta:
        model = Task
        fields = ['status']
    
    def update(self, instance, validated_data):
        if validated_data.get('status') == 'COMPLETED':
            instance.completed_at = timezone.now()
        return super().update(instance, validated_data)

class TaskCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ['comment']