from rest_framework import serializers
from django.utils import timezone
from .models import DailyReport, MonthlyReport, SalaryRecord
from apps.users.serializers import UserSerializer

class DailyReportSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    class Meta:
        model = DailyReport
        fields = ['id', 'student', 'report_date', 'hours_worked', 'work_description', 'created_at']
        read_only_fields = ['student', 'created_at']

    def validate_report_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajak uchun hisobot yozib bo'lmaydi.")
        if DailyReport.objects.filter(student=self.context['request'].user, report_date=value).exists():
            raise serializers.ValidationError(f"{value} sanasi uchun hisobot allaqachon mavjud.")
        return value
    
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)

class SalaryRecordSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    class Meta:
        model = SalaryRecord
        fields = '__all__'

class MonthlyReportSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    salary = SalaryRecordSerializer(read_only=True)
    file = serializers.FileField(read_only=True)
    class Meta:
        model = MonthlyReport
        fields = ['id', 'student', 'salary', 'month', 'year', 'file', 'status', 'managed_by', 'rejection_reason']

class MonthlyReportManageSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=(('APPROVED', 'Tasdiqlangan'), ('REJECTED', 'Rad etilgan')))
    rejection_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    def validate(self, data):
        if data.get('status') == 'REJECTED' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rad etish uchun sabab ko'rsatish shart."})
        return data

class SalaryPaidSerializer(serializers.Serializer):
    pass