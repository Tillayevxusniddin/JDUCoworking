# apps/notifications/serializers.py

from rest_framework import serializers
from .models import Notification

# YORDAMCHI OPTIMALLASHTIRILGAN SERIALIZER'LARNI IMPORT QILAMIZ
from apps.users.serializers import UserSummarySerializer

# ====================================================================
# 1. Barcha modellar uchun universal, qisqa ma'lumot beruvchi serializer
# ====================================================================
class GenericObjectSummarySerializer(serializers.Serializer):
    """
    Istalgan obyekt uchun qisqa ma'lumot (ID va matnli ko'rinish) qaytaradi.
    Bu ro'yxatlar uchun ishlatiladi.
    """
    id = serializers.IntegerField()
    object_type = serializers.CharField(source='_meta.model_name')
    display_text = serializers.CharField(source='__str__')

# ====================================================================
# 2. GenericForeignKey'ni o'qish uchun aqlli maydon
# ====================================================================
class SmartGenericRelatedField(serializers.RelatedField):
    """
    Context'ga (list yoki detail) qarab GenericForeignKey'ni to'g'ri
    serialize qiladigan maxsus maydon.
    """
    def to_representation(self, value):
        if 'view' in self.context and self.context['view'].action == 'list':
            return GenericObjectSummarySerializer(value).data
        
        # Circular Import'ning oldini olish uchun funksiya ichida import qilamiz
        from apps.tasks.serializers import TaskDetailSerializer
        from apps.meetings.serializers import MeetingDetailSerializer
        from apps.workspaces.serializers import WorkspaceDetailSerializer
        from apps.reports.serializers import MonthlyReportDetailSerializer, SalaryRecordDetailSerializer
        from apps.jobs.serializers import VacancyApplicationDetailSerializer, JobVacancyDetailSerializer

        serializer_map = {
            'task': TaskDetailSerializer,
            'meeting': MeetingDetailSerializer,
            'workspace': WorkspaceDetailSerializer,
            'monthlyreport': MonthlyReportDetailSerializer,
            'salaryrecord': SalaryRecordDetailSerializer,
            'vacancyapplication': VacancyApplicationDetailSerializer,
            'jobvacancy': JobVacancyDetailSerializer,
        }
        
        model_name = value._meta.model_name
        serializer_class = serializer_map.get(model_name)

        if serializer_class:
            return serializer_class(value, context=self.context).data
        
        return GenericObjectSummarySerializer(value).data

# ====================================================================
# 3. Asosiy Notification Serializer'lari
# ====================================================================
class NotificationBaseSerializer(serializers.ModelSerializer):
    """Bildirishnomalar uchun asosiy maydonlar."""
    actor = UserSummarySerializer(read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor', 'verb', 'message', 'is_read', 'created_at']

class NotificationListSerializer(NotificationBaseSerializer):
    """Bildirishnomalar ro'yxati uchun qisqa ma'lumot."""
    action_object = GenericObjectSummarySerializer(read_only=True)
    target = GenericObjectSummarySerializer(read_only=True)

    class Meta(NotificationBaseSerializer.Meta):
        fields = NotificationBaseSerializer.Meta.fields + ['action_object', 'target']

class NotificationDetailSerializer(NotificationBaseSerializer):
    """Bitta bildirishnoma uchun batafsil ma'lumot."""
    action_object = SmartGenericRelatedField(read_only=True)
    target = SmartGenericRelatedField(read_only=True)

    class Meta(NotificationBaseSerializer.Meta):
        fields = NotificationBaseSerializer.Meta.fields + ['action_object', 'target']
    """
    Barcha bildirishnomalar uchun asosiy serializer.
    """
    actor = UserSummarySerializer(read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # ✅ TUZATILGAN QISM: XATO DEKORATORLAR OLIB TASHLAΝDI
    action_object = SmartGenericRelatedField(read_only=True)
    target = SmartGenericRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 
            'recipient', 
            'actor', 
            'verb', 
            'message', 
            'is_read', 
            'created_at',
            'action_object',
            'target'
        ]
