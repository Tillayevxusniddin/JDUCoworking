from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from .models import Workspace, WorkspaceMember
from apps.users.serializers import UserSerializer

class WorkspaceSerializer(serializers.ModelSerializer):
    active_members_count = serializers.IntegerField(read_only=True)
    workspace_type_display = serializers.SerializerMethodField()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_workspace_type_display(self, obj):
        return obj.get_workspace_type_display()

    class Meta:
        model = Workspace
        fields = [
            'id', 'name', 'description', 'created_by', 'is_active',
            'max_members', 'workspace_type', 'workspace_type_display',
            'created_at', 'updated_at', 'active_members_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'active_members_count']

class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    role_display = serializers.SerializerMethodField()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_role_display(self, obj):
        return obj.get_role_display()

    class Meta:
        model = WorkspaceMember
        fields = [
            'id', 'workspace', 'user', 'role', 'role_display',
            'joined_at', 'is_active', 'last_activity'
        ]
        read_only_fields = ['id', 'joined_at', 'last_activity', 'workspace', 'user']

class WorkspaceMemberCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    role = serializers.ChoiceField(choices=WorkspaceMember.MEMBER_ROLE_CHOICES, default='MEMBER')
    workspace_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = WorkspaceMember
        fields = ['user_id', 'workspace_id', 'role', 'is_active']

    def validate(self, data):
        # Schema yaratish jarayonida tekshiruvlarni o'tkazib yuborish
        if getattr(self, 'swagger_fake_view', False):
            return data
            
        workspace_id = data.get('workspace_id') or self.context.get('view').kwargs.get('pk')
        user_id = data.get('user_id')
        
        if workspace_id and user_id:
            if WorkspaceMember.objects.filter(user_id=user_id, workspace_id=workspace_id).exists():
                raise serializers.ValidationError("Bu foydalanuvchi allaqachon ushbu workspace a'zosi.")
                
        return data

    def create(self, validated_data):
        workspace_id = validated_data.pop('workspace_id', None) or self.context.get('view').kwargs.get('pk')
        user_id = validated_data.pop('user_id')
        return WorkspaceMember.objects.create(
            user_id=user_id,
            workspace_id=workspace_id,
            **validated_data
        )