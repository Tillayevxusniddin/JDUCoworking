# apps/jobs/serializers.py

from rest_framework import serializers
from .models import Job, JobVacancy, VacancyApplication
from apps.users.models import User

# YORDAMCHI OPTIMALLASHTIRILGAN SERIALIZER'LARNI IMPORT QILAMIZ
from apps.users.serializers import UserSummarySerializer
from apps.workspaces.serializers import WorkspaceSummarySerializer


# ----------------- Job (Loyiha) Serializers -----------------

class JobSummarySerializer(serializers.ModelSerializer):
    """Loyiha haqida qisqa ma'lumot (ID, sarlavha)."""
    class Meta:
        model = Job
        fields = ['id', 'title', 'status']

class JobListSerializer(serializers.ModelSerializer):
    """Loyihalar ro'yxati uchun optimallashtirilgan serializer."""
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'title', 'status', 'status_display', 'workspace', 'created_by']

class JobDetailSerializer(serializers.ModelSerializer):
    """Bitta loyiha uchun batafsil ma'lumot."""
    workspace = WorkspaceSummarySerializer(read_only=True)
    created_by = UserSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Job
        fields = '__all__'


# ----------------- JobVacancy (Vakansiya) Serializers -----------------

class JobVacancySummarySerializer(serializers.ModelSerializer):
    """Vakansiya haqida qisqa ma'lumot (ID, sarlavha)."""
    job = JobSummarySerializer(read_only=True)
    class Meta:
        model = JobVacancy
        fields = ['id', 'title', 'job']

class JobVacancyListSerializer(serializers.ModelSerializer):
    """Vakansiyalar ro'yxati uchun optimallashtirilgan serializer."""
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = JobVacancy
        fields = ['id', 'title', 'job', 'status', 'status_display', 'slots_available', 'application_deadline', 'created_by']

class JobVacancyDetailSerializer(serializers.ModelSerializer):
    """Bitta vakansiya uchun batafsil ma'lumot."""
    job = JobDetailSerializer(read_only=True) # Bu yerda Job haqida to'liq ma'lumot beramiz
    created_by = UserSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = JobVacancy
        fields = '__all__'


# ----------------- VacancyApplication (Ariza) Serializers -----------------

class VacancyApplicationListSerializer(serializers.ModelSerializer):
    """Arizalar ro'yxati uchun optimallashtirilgan serializer."""
    vacancy = serializers.PrimaryKeyRelatedField(read_only=True)
    applicant = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VacancyApplication
        fields = ['id', 'vacancy', 'applicant', 'status', 'status_display', 'applied_at']

class VacancyApplicationDetailSerializer(serializers.ModelSerializer):
    """Bitta ariza uchun batafsil ma'lumot."""
    applicant = UserSummarySerializer(read_only=True)
    vacancy = JobVacancySummarySerializer(read_only=True) # Vakansiya haqida qisqa ma'lumot
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VacancyApplication
        fields = '__all__'


# ----------------- Create / Update Serializers (o'zgarishsiz) -----------------

class JobCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['title', 'description', 'base_hourly_rate', 'status']

class JobVacancyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobVacancy
        fields = ['job', 'title', 'description', 'requirements', 'slots_available', 'application_deadline', 'status']

class VacancyApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyApplication
        fields = ['vacancy', 'cover_letter']

    def validate_vacancy(self, vacancy):
        if vacancy.status != 'OPEN':
            raise serializers.ValidationError("Bu vakansiya uchun arizalar qabuli yopilgan.")
        user = self.context['request'].user
        if VacancyApplication.objects.filter(vacancy=vacancy, applicant=user).exists():
            raise serializers.ValidationError("Siz bu vakansiyaga allaqachon ariza topshirgansiz.")
        return vacancy

class VacancyApplicationManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyApplication
        fields = ['status', 'notes']
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request:
            instance._reviewed_by_user = request.user
        return super().update(instance, validated_data)
