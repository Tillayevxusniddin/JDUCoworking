# apps/meetings/serializers.py

from rest_framework import serializers
from .models import Meeting, MeetingAttendee
from apps.users.models import User
# ✅ YORDAMCHI OPTIMALLASHTIRILGAN SERIALIZER'LARNI IMPORT QILAMIZ
from apps.users.serializers import UserSummarySerializer
from apps.workspaces.serializers import WorkspaceSummarySerializer
from apps.workspaces.models import Workspace

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


# ----------------- MeetingAttendee Serializers -----------------

class MeetingAttendeeListSerializer(serializers.ModelSerializer):
    """Qatnashuvchilar ro'yxati uchun optimallashtirilgan serializer."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MeetingAttendee
        fields = ['id', 'user', 'status', 'status_display']

class MeetingAttendeeDetailSerializer(serializers.ModelSerializer):
    """Bitta qatnashuvchi uchun batafsil ma'lumot."""
    user = UserSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MeetingAttendee
        fields = ['id', 'user', 'status', 'status_display', 'responded_at']


# ----------------- Meeting Serializers -----------------

class MeetingListSerializer(serializers.ModelSerializer):
    """Uchrashuvlar ro'yxati uchun optimallashtirilgan serializer."""
    organizer = serializers.PrimaryKeyRelatedField(read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attendees_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'organizer', 'workspace', 'start_time', 'end_time', 
            'status', 'status_display', 'attendees_count'
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_attendees_count(self, obj):
        # .count() dan foydalanish .all() dan ko'ra samaraliroq
        return obj.attendees.count()

class MeetingDetailSerializer(serializers.ModelSerializer):
    """Bitta uchrashuv uchun batafsil ma'lumot."""
    organizer = UserSummarySerializer(read_only=True)
    workspace = WorkspaceSummarySerializer(read_only=True, allow_null=True)
    # ✅ Qatnashuvchilar ro'yxatini ham optimallashtirilgan serializer bilan ko'rsatamiz
    attendees = MeetingAttendeeListSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    audience_type_display = serializers.CharField(source='get_audience_type_display', read_only=True)

    class Meta:
        model = Meeting
        fields = '__all__'


# ----------------- Create / Update Serializers (o'zgarishsiz) -----------------

class MeetingCreateSerializer(serializers.ModelSerializer):
    invited_users = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all()),
        required=False,
        write_only=True
    )
    workspace = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(),
        required=False, # Endi majburiy emas, audience_type ga bog'liq
        allow_null=True
    )

    class Meta:
        model = Meeting
        fields = [
            'title', 'description', 'workspace', 'start_time', 'end_time',
            'audience_type', 'invited_users'
        ]

    def validate(self, data):
        # ... mavjud validatsiya mantiqi o'zgarishsiz qoladi ...
        if data.get('start_time') >= data.get('end_time'):
            raise serializers.ValidationError("Uchrashuvning tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak.")
        if data.get('audience_type') == Meeting.AudienceType.WORKSPACE_MEMBERS and not data.get('workspace'):
            raise serializers.ValidationError({"workspace": "Bu turdagi uchrashuv uchun ish maydoni ko'rsatilishi shart."})
        if data.get('audience_type') == Meeting.AudienceType.SPECIFIC_USERS and not data.get('invited_users'):
            raise serializers.ValidationError({"invited_users": "Bu turdagi uchrashuv uchun foydalanuvchilar ro'yxati bo'sh bo'lishi mumkin emas."})
        return data

class AttendeeStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingAttendee
        fields = ['status']
    
    def validate_status(self, value):
        if value not in [MeetingAttendee.Status.ACCEPTED, MeetingAttendee.Status.DECLINED]:
            raise serializers.ValidationError("Siz faqat 'ACCEPTED' yoki 'DECLINED' statusini tanlay olasiz.")
        return value

class MeetingLinkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = ['meeting_link']
    
    def validate_meeting_link(self, value):
        if not value.startswith("https://meet.google.com/"):
            raise serializers.ValidationError("Iltimos, to'g'ri Google Meet havolasini kiriting.")
        return value