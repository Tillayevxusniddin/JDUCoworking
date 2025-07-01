from rest_framework import serializers
from django.utils import timezone
from .models import DailyReport, MonthlyReport, SalaryRecord
from apps.users.serializers import UserSerializer


class DailyReportSerializer(serializers.ModelSerializer):
    """Kunlik hisobotlarni yaratish va ko'rish uchun."""
    student = UserSerializer(read_only=True)

    class Meta:
        model = DailyReport
        fields = ['id', 'student', 'report_date', 'hours_worked', 'work_description', 'created_at', 'updated_at']
        read_only_fields = ['student', 'created_at', 'updated_at']
    def validate_report_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajakdagi sana uchun hisobot yozib bo'lmaydi.")
        return value
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)
    
class SalaryRecordSerializer(serializers.ModelSerializer):
    """Oylik maosh yozuvlarini ko'rsatish uchun."""
    student = UserSerializer(read_only=True)

    class Meta:
        model = SalaryRecord
        fields = '__all__'

class MonthlyReportSerializer(serializers.ModelSerializer):
    """Oylik hisobotlarni ko'rsatish uchun."""
    student = UserSerializer(read_only=True)
    salary = SalaryRecordSerializer(read_only=True)
    file_url = serializers.FileField(source='file', read_only=True)

    class Meta:
        model = MonthlyReport
        fields = ['id', 'student', 'salary', 'month', 'year', 'file_url', 'status', 'managed_by', 'rejection_reason', 'created_at']

class MonthlyReportManageSerializer(serializers.Serializer):
    """Oylik hisobotni tasdiqlash/rad etish uchun."""
    STATUS_CHOICES = (('APPROVED', 'Tasdiqlangan'), ('REJECTED', 'Rad etilgan'))
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    rejection_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if data.get('status') == 'REJECTED' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Hisobotni rad etish uchun sabab ko'rsatilishi shart."})
        return data

class SalaryPaidSerializer(serializers.Serializer):
    """Maosh to'langanini belgilash uchun bo'sh serializer."""
    pass