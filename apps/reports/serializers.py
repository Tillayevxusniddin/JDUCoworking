# apps/reports/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import DailyReport, MonthlyReport, SalaryRecord
from apps.users.models import User
from apps.workspaces.models import WorkspaceMember, Workspace

from apps.users.serializers import UserSummarySerializer
from apps.workspaces.serializers import WorkspaceSummarySerializer


# ----------------- DailyReport Serializers -----------------

class DailyReportListSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DailyReport
        fields = ['id', 'student', 'workspace', 'report_date', 'hours_worked']

class DailyReportDetailSerializer(serializers.ModelSerializer):
    student = UserSummarySerializer(read_only=True)
    workspace = WorkspaceSummarySerializer(read_only=True)

    class Meta:
        model = DailyReport
        fields = '__all__'

class DailyReportCreateSerializer(serializers.ModelSerializer):
    workspace_id = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(),
        write_only=True,
        source='workspace'
    )
    class Meta:
        model = DailyReport
        fields = ['workspace_id', 'report_date', 'hours_worked', 'work_description']

    def validate(self, data):
        user = self.context['request'].user
        workspace = data.get('workspace')
        report_date = data.get('report_date')
        if report_date > timezone.now().date():
            raise serializers.ValidationError({"report_date": "You cannot create a report for a future date."})
        if not WorkspaceMember.objects.filter(user=user, workspace=workspace, is_active=True).exists():
            raise serializers.ValidationError({"workspace_id": "You are not a member of this workspace."})
        if DailyReport.objects.filter(student=user, report_date=report_date, workspace=workspace).exists():
            raise serializers.ValidationError(f"A report already exists for {report_date} in this workspace.")
        return data

# ----------------- SalaryRecord Serializers -----------------

class SalaryRecordListSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SalaryRecord
        fields = ['id', 'student', 'workspace', 'year', 'month', 'net_amount', 'status', 'status_display']

class SalaryRecordDetailSerializer(serializers.ModelSerializer):
    student = UserSummarySerializer(read_only=True)
    workspace = WorkspaceSummarySerializer(read_only=True)
    approved_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = SalaryRecord
        fields = '__all__'

# ----------------- MonthlyReport Serializers -----------------

class MonthlyReportListSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    salary = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MonthlyReport
        fields = ['id', 'student', 'workspace', 'salary', 'month', 'year', 'status', 'status_display']

class MonthlyReportDetailSerializer(serializers.ModelSerializer):
    student = UserSummarySerializer(read_only=True)
    workspace = WorkspaceSummarySerializer(read_only=True)
    salary = SalaryRecordDetailSerializer(read_only=True)
    managed_by = UserSummarySerializer(read_only=True)
    file = serializers.FileField(read_only=True)

    class Meta:
        model = MonthlyReport
        fields = '__all__'


# ----------------- Action Serializers (o'zgarishsiz) -----------------

class MonthlyReportManageSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=(('APPROVED', 'Approved'), ('REJECTED', 'Rejected')))
    rejection_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    def validate(self, data):
        if data.get('status') == 'REJECTED' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "A rejection reason must be provided."})
        return data

class SalaryPaidSerializer(serializers.Serializer):
    pass