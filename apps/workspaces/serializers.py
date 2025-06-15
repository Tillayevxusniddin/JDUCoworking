from rest_framework import serializers
from .models import Workspace, WorkspaceMember
from apps.users.serializers import UserSerializer

class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    active_members_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workspace
        fields = [
            'id',
            'name',
            'description',
            'created_by',
            'is_active',
            'max_members',
            'workspace_type',
            'created_at',
            'updated_at',
            'active_members_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'active_members_count']

        def create(self, validated_data):
            user = self.context['request'].user
            validated_data['created_by'] = user
            workspace = Workspace.objects.create(**validated_data)
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=user,
                role='ADMIN'  # Default role for the creator
            )
            return workspace
        
        def update(self, instance, validated_data):
            return super().update(instance, validated_data)


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'role', 'joined_date', 'is_active', 'last_activity']
        read_only_fields = ['id', 'joined_date', 'last_activity', 'workspace', 'user']


class WorkspaceMemberCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    workspace_id = serializers.IntegerField(write_only=True)
    role = serializers.ChoiceField(choices=WorkspaceMember.MEMBER_ROLE_CHOICES, default='MEMBER')

    class Meta:
        model = WorkspaceMember
        fields = ['user_id', 'workspace_id', 'role', 'is_active']

    def validate(self, data):
        user_id = data.get('user_id')
        workspace_id = data.get('workspace_id')
        if WorkspaceMember.objects.filter(user_id=user_id, workspace_id=workspace_id).exists():
            raise serializers.ValidationError("Bu foydalanuvchi allaqachon ushbu workspace a'zosi.")
        return data
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        workspace_id = validated_data.pop('workspace_id')
        return WorkspaceMember.objects.create(
            user_id=user_id,
            workspace_id=workspace_id,
            **validated_data
        )


