# apps/workspaces/serializers.py

from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from .models import Workspace, WorkspaceMember
from apps.users.models import User
# ✅ O'ZGARISH: UserSummarySerializer'ni import qilamiz
from apps.users.serializers import UserSummarySerializer

# ----------------- Workspace Serializers -----------------

class WorkspaceSummarySerializer(serializers.ModelSerializer):
    """Ish maydonining qisqa ma'lumotlarini (ID, nom) qaytaradi."""
    class Meta:
        model = Workspace
        fields = ['id', 'name']

class WorkspaceDetailSerializer(serializers.ModelSerializer):
    """Bitta ish maydoni uchun to'liq ma'lumot."""
    created_by = UserSummarySerializer(read_only=True) # ✅ To'liq emas, qisqa ma'lumot

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
    """Ish maydonlari ro'yxati uchun qisqa ma'lumot."""
    # ✅ O'ZGARISH: `created_by` endi faqat ID qaytaradi
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    active_members_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'workspace_type', 'active_members_count', 'created_by']


# ----------------- WorkspaceMember Serializers -----------------

class WorkspaceMemberDetailSerializer(serializers.ModelSerializer):
    """Bitta ish maydoni a'zosi uchun to'liq ma'lumot."""
    user = UserSummarySerializer(read_only=True) # ✅ Qisqa ma'lumot
    workspace = WorkspaceSummarySerializer(read_only=True) # ✅ Qisqa ma'lumot
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = [
            'id', 'workspace', 'user', 'role', 'role_display',
            'hourly_rate_override', 'joined_at', 'is_active'
        ]

class WorkspaceMemberListSerializer(serializers.ModelSerializer):
    """Ish maydoni a'zolari ro'yxati uchun qisqa ma'lumot."""
    # ✅ O'ZGARISH: Bog'liqliklar faqat ID'lar bilan qaytariladi
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
        label="Foydalanuvchi ID"
    )
    class Meta:
        model = WorkspaceMember
        fields = ['user_id', 'is_active']
    # ... qolgan validate va create metodlari o'zgarishsiz ...
    def validate(self, data):
        if getattr(self, 'swagger_fake_view', False): return data
        workspace_id = self.context['view'].kwargs.get('pk')
        user = data.get('user_id')
        if WorkspaceMember.objects.filter(user=user, workspace_id=workspace_id).exists():
            raise serializers.ValidationError({"user_id": "Bu foydalanuvchi allaqachon ushbu ish maydoniga a'zo."})
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
        if not role: raise serializers.ValidationError("Foydalanuvchi uchun rol aniqlanmadi.")
        return WorkspaceMember.objects.create(user=user, workspace_id=workspace_id, role=role, **validated_data)

class WorkspaceMemberRateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceMember
        fields = ['hourly_rate_override']