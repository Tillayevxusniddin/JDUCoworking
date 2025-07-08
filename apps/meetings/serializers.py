# apps/meetings/serializers.py
from rest_framework import serializers
from .models import Meeting, MeetingAttendee
from apps.users.serializers import UserSerializer

class MeetingAttendeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = MeetingAttendee
        fields = ['id', 'user', 'status', 'responded_at']

class MeetingSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    attendees = MeetingAttendeeSerializer(many=True, read_only=True)
    class Meta:
        model = Meeting
        fields = '__all__'

class MeetingCreateSerializer(serializers.ModelSerializer):
    # Agar 'SPECIFIC_USERS' tanlansa, bu maydonga user ID'lari yoziladi
    invited_users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    class Meta:
        model = Meeting
        fields = [
            'title', 'description', 'workspace', 'start_time', 'end_time',
            'audience_type', 'invited_users'
        ]

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Uchrashuvning tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak.")
        if data.get('audience_type') == Meeting.AudienceType.WORKSPACE_MEMBERS and not data.get('workspace'):
            raise serializers.ValidationError({"workspace": "Bu turdagi uchrashuv uchun ish maydoni ko'rsatilishi shart."})
        if data.get('audience_type') == Meeting.AudienceType.SPECIFIC_USERS and not data.get('invited_users'):
            raise serializers.ValidationError({"invited_users": "Bu turdagi uchrashuv uchun foydalanuvchilar ro'yxati bo'sh bo'lishi mumkin emas."})
        return data

    def create(self, validated_data):
        invited_users_ids = validated_data.pop('invited_users', [])
        validated_data['organizer'] = self.context['request'].user
        meeting = super().create(validated_data)

        if invited_users_ids:
            attendees_to_create = [
                MeetingAttendee(meeting=meeting, user_id=user_id) for user_id in invited_users_ids
            ]
            MeetingAttendee.objects.bulk_create(attendees_to_create, ignore_conflicts=True)
            
        return meeting

class AttendeeStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingAttendee
        fields = ['status']
        
    def validate_status(self, value):
        if value not in [MeetingAttendee.Status.ACCEPTED, MeetingAttendee.Status.DECLINED]:
            raise serializers.ValidationError("Siz faqat 'ACCEPTED' yoki 'DECLINED' statusini tanlay olasiz.")
        return value

class MeetingLinkUpdateSerializer(serializers.ModelSerializer):
    """Faqat meeting_link'ni yangilash uchun."""
    class Meta:
        model = Meeting
        fields = ['meeting_link']
    
    def validate_meeting_link(self, value):
        if not value.startswith("https://meet.google.com/"):
            raise serializers.ValidationError("Iltimos, to'g'ri Google Meet havolasini kiriting.")
        return value