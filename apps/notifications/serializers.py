# apps/notifications/serializers.py

from rest_framework import serializers
from .models import Notification

from apps.users.serializers import UserSummarySerializer

# ====================================================================
# 1. Universal Serializer for GenericForeignKey objects
# ====================================================================
class GenericObjectSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    object_type = serializers.CharField(source='_meta.model_name')
    display_text = serializers.CharField(source='__str__')

# ====================================================================
# 2. Smart field to read GenericForeignKey
# ====================================================================
class SmartGenericRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        if 'view' in self.context and self.context['view'].action == 'list':
            return GenericObjectSummarySerializer(value).data
        
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
# 3. General Notification Serializer
# ====================================================================
class NotificationBaseSerializer(serializers.ModelSerializer):
    actor = UserSummarySerializer(read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor', 'verb', 'message', 'is_read', 'created_at']

class NotificationListSerializer(NotificationBaseSerializer):
    action_object = GenericObjectSummarySerializer(read_only=True)
    target = GenericObjectSummarySerializer(read_only=True)

    class Meta(NotificationBaseSerializer.Meta):
        fields = NotificationBaseSerializer.Meta.fields + ['action_object', 'target']

class NotificationDetailSerializer(NotificationBaseSerializer):
    action_object = SmartGenericRelatedField(read_only=True)
    target = SmartGenericRelatedField(read_only=True)

    class Meta(NotificationBaseSerializer.Meta):
        fields = NotificationBaseSerializer.Meta.fields + ['action_object', 'target']
        
    actor = UserSummarySerializer(read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(read_only=True)
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
