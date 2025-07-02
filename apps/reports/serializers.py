# apps/reports/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import DailyReport, MonthlyReport, SalaryRecord
from apps.users.serializers import UserSerializer
from apps.workspaces.models import WorkspaceMember
from apps.workspaces.serializers import WorkspaceSerializer

class DailyReportSerializer(serializers.ModelSerializer):
    """Kunlik hisobotlarni yaratish va ko'rish uchun."""
    student = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    workspace_id = serializers.IntegerField(write_only=True, label="Ish Maydoni IDsi")

    class Meta:
        model = DailyReport
        fields = ['id', 'student', 'workspace', 'workspace_id', 'report_date', 'hours_worked', 'work_description', 'created_at']
        read_only_fields = ['student', 'workspace', 'created_at']

    def validate(self, data):
        user = self.context['request'].user
        workspace_id = data.get('workspace_id')
        report_date = data.get('report_date')

        if report_date > timezone.now().date():
            raise serializers.ValidationError({"report_date": "Kelajakdagi sana uchun hisobot yozib bo'lmaydi."})
        
        if not WorkspaceMember.objects.filter(user=user, workspace_id=workspace_id, is_active=True).exists():
            raise serializers.ValidationError({"workspace_id": "Siz bu ish maydonining a'zosi emassiz."})

        if DailyReport.objects.filter(student=user, report_date=report_date, workspace_id=workspace_id).exists():
            raise serializers.ValidationError(f"{report_date} sanasida bu ish maydoni uchun hisobot allaqachon mavjud.")
            
        return data
    
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)

class SalaryRecordSerializer(serializers.ModelSerializer):
    """Oylik maosh yozuvlarini ko'rsatish uchun."""
    student = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    class Meta:
        model = SalaryRecord
        fields = '__all__'

class MonthlyReportSerializer(serializers.ModelSerializer):
    """Oylik hisobotlarni ko'rsatish uchun."""
    student = UserSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)
    salary = SalaryRecordSerializer(read_only=True)
    file = serializers.FileField(read_only=True)

    class Meta:
        model = MonthlyReport
        fields = ['id', 'student', 'workspace', 'salary', 'month', 'year', 'file', 'status', 'managed_by', 'rejection_reason']

class MonthlyReportManageSerializer(serializers.Serializer):
    """Oylik hisobotni tasdiqlash/rad etish uchun."""
    status = serializers.ChoiceField(choices=(('APPROVED', 'Tasdiqlangan'), ('REJECTED', 'Rad etilgan')))
    rejection_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    def validate(self, data):
        if data.get('status') == 'REJECTED' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rad etish uchun sabab ko'rsatish shart."})
        return data

class SalaryPaidSerializer(serializers.Serializer):
    """Maosh to'langanini belgilash uchun bo'sh serializer."""
    pass