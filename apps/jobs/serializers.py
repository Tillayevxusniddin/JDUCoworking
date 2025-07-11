# apps/jobs/serializers.py

from rest_framework import serializers
from .models import Job, JobVacancy, VacancyApplication
from apps.users.models import User

from apps.users.serializers import UserSummarySerializer
from apps.workspaces.serializers import WorkspaceSummarySerializer


class JobSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'status']

class JobListSerializer(serializers.ModelSerializer):
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'title', 'status', 'status_display', 'workspace', 'created_by']

class JobDetailSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSummarySerializer(read_only=True)
    created_by = UserSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Job
        fields = '__all__'


class JobVacancySummarySerializer(serializers.ModelSerializer):
    job = JobSummarySerializer(read_only=True)
    class Meta:
        model = JobVacancy
        fields = ['id', 'title', 'job']

class JobVacancyListSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = JobVacancy
        fields = ['id', 'title', 'job', 'status', 'status_display', 'slots_available', 'application_deadline', 'created_by']

class JobVacancyDetailSerializer(serializers.ModelSerializer):
    job = JobDetailSerializer(read_only=True) 
    created_by = UserSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = JobVacancy
        fields = '__all__'

class VacancyApplicationListSerializer(serializers.ModelSerializer):
    vacancy = serializers.PrimaryKeyRelatedField(read_only=True)
    applicant = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VacancyApplication
        fields = ['id', 'vacancy', 'applicant', 'status', 'status_display', 'applied_at']

class VacancyApplicationDetailSerializer(serializers.ModelSerializer):
    applicant = UserSummarySerializer(read_only=True)
    vacancy = JobVacancySummarySerializer(read_only=True) 
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VacancyApplication
        fields = '__all__'

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
            raise serializers.ValidationError("This vacancy is not open for applications.")
        user = self.context['request'].user
        if VacancyApplication.objects.filter(vacancy=vacancy, applicant=user).exists():
            raise serializers.ValidationError("You have already applied for this vacancy.")
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
