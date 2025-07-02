# apps/workspaces/serializers.py

from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from .models import Workspace, WorkspaceMember
# --- KERAKLI IMPORTLAR ---
from apps.users.models import User
from apps.users.serializers import UserSerializer
# -------------------------

class WorkspaceSerializer(serializers.ModelSerializer):
    # Bu serializer o'zgarishsiz qoladi
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
    # Bu serializer o'zgarishsiz qoladi
    user = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = [
            'id', 'workspace', 'user', 'role', 'role_display',
            'joined_at', 'is_active', 'last_activity'
        ]
        read_only_fields = ['id', 'joined_at', 'last_activity', 'workspace', 'user', 'role', 'role_display']

class WorkspaceMemberCreateSerializer(serializers.ModelSerializer):
    # --- SERIALIZER YANGILANDI ---
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        label="Foydalanuvchi ID"
    )

    class Meta:
        model = WorkspaceMember
        fields = ['user_id', 'is_active'] # `role` va `workspace_id` olib tashlandi

    def validate(self, data):
        if getattr(self, 'swagger_fake_view', False):
            return data
            
        workspace_id = self.context['view'].kwargs.get('pk')
        user = data.get('user_id')
        
        if WorkspaceMember.objects.filter(user=user, workspace_id=workspace_id).exists():
            raise serializers.ValidationError({"user_id": "Bu foydalanuvchi allaqachon ushbu ish maydoniga a'zo."})
            
        return data

    def create(self, validated_data):
        workspace_id = self.context['view'].kwargs.get('pk')
        user = validated_data.pop('user_id')
        
        # --- ROLNI AVTOMATIK ANIQLASH MANTIG'I ---
        role = ""
        if user.user_type == 'ADMIN':
            role = 'ADMIN'
        elif user.user_type == 'STAFF':
            role = 'STAFF'
        elif user.user_type == 'RECRUITER':
            role = 'RECRUITER'
        elif user.user_type == 'STUDENT':
            try:
                if user.student_profile.level_status == 'TEAMLEAD':
                    role = 'TEAMLEADER'
                else:  # SIMPLE
                    role = 'STUDENT'
            except User.student_profile.RelatedObjectDoesNotExist:
                # Agar studentning profili bo'lmasa (kam ehtimol), oddiy student deb hisoblaymiz
                role = 'STUDENT'
        
        if not role:
            # Bu holat deyarli yuzaga kelmaydi, lekin har ehtimolga qarshi
            raise serializers.ValidationError("Foydalanuvchi uchun rol aniqlanmadi.")
        # ---------------------------------------------
        
        return WorkspaceMember.objects.create(
            user=user,
            workspace_id=workspace_id,
            role=role,
            **validated_data
        )
    
class WorkspaceMemberRateUpdateSerializer(serializers.ModelSerializer):
    """Staff/Admin tomonidan a'zoning shaxsiy stavkasini yangilash uchun."""
    class Meta:
        model = WorkspaceMember
        fields = ['hourly_rate_override']