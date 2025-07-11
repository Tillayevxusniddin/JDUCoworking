# apps/workspaces/serializers.py

from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from .models import Workspace, WorkspaceMember
from apps.users.models import User
from apps.users.serializers import UserSummarySerializer

# ----------------- Workspace Serializers -----------------

class WorkspaceSummarySerializer(serializers.ModelSerializer):
    """short summary of a workspace, used in lists."""
    class Meta:
        model = Workspace
        fields = ['id', 'name']

class WorkspaceDetailSerializer(serializers.ModelSerializer):
    """Detailed information about a workspace, used in detail views."""
    created_by = UserSummarySerializer(read_only=True) 

    active_members_count = serializers.IntegerField(read_only=True)
    workspace_type_display = serializers.CharField(source='get_workspace_type_display', read_only=True)

    class Meta:
        model = Workspace
        fields = [
            'id', 'name', 'description', 'created_by', 'is_active',
            'max_members', 'workspace_type', 'workspace_type_display',
            'created_at', 'updated_at', 'active_members_count'
        ]

class WorkspaceListSerializer(serializers.ModelSerializer):
    """short summary of workspaces for list views."""
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    active_members_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'workspace_type', 'active_members_count', 'created_by']


# ----------------- WorkspaceMember Serializers -----------------

class WorkspaceMemberDetailSerializer(serializers.ModelSerializer):
    """Detailed information about a workspace member."""
    user = UserSummarySerializer(read_only=True)
    workspace = WorkspaceSummarySerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = [
            'id', 'workspace', 'user', 'role', 'role_display',
            'hourly_rate_override', 'joined_at', 'is_active'
        ]

class WorkspaceMemberListSerializer(serializers.ModelSerializer):
    """short summary of workspace members for list views."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'user', 'workspace', 'role', 'role_display', 'is_active']


# ----------------- Create / Update Serializers (o'zgarishsiz) -----------------

class WorkspaceMemberCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        label="User ID",
        help_text="ID of the user to be added as a member."
    )
    class Meta:
        model = WorkspaceMember
        fields = ['user_id', 'is_active']
    def validate(self, data):
        if getattr(self, 'swagger_fake_view', False): return data
        workspace_id = self.context['view'].kwargs.get('pk')
        user = data.get('user_id')
        if WorkspaceMember.objects.filter(user=user, workspace_id=workspace_id).exists():
            raise serializers.ValidationError({"user_id": "This user is already a member of the workspace."})
        return data
    def create(self, validated_data):
        workspace_id = self.context['view'].kwargs.get('pk')
        user = validated_data.pop('user_id')
        role = ""
        if user.user_type == 'ADMIN': role = 'ADMIN'
        elif user.user_type == 'STAFF': role = 'STAFF'
        elif user.user_type == 'RECRUITER': role = 'RECRUITER'
        elif user.user_type == 'STUDENT':
            try:
                if user.student_profile.level_status == 'TEAMLEAD': role = 'TEAMLEADER'
                else: role = 'STUDENT'
            except User.student_profile.RelatedObjectDoesNotExist: role = 'STUDENT'
        if not role: raise serializers.ValidationError("Role could not be determined for the user.")
        return WorkspaceMember.objects.create(user=user, workspace_id=workspace_id, role=role, **validated_data)

class WorkspaceMemberRateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceMember
        fields = ['hourly_rate_override']