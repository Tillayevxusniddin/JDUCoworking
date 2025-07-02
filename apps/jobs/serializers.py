# apps/jobs/serializers.py
from rest_framework import serializers
from .models import Job, JobVacancy, VacancyApplication
from apps.users.serializers import UserSerializer

# --- Job (Loyiha) Serializers ---
class JobSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    class Meta:
        model = Job
        fields = '__all__'

class JobCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['title', 'description', 'base_hourly_rate', 'status']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

# --- JobVacancy (Vakansiya) Serializers ---
class JobVacancySerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    class Meta:
        model = JobVacancy
        fields = '__all__'

class JobVacancyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobVacancy
        fields = ['job', 'title', 'description', 'requirements', 'slots_available', 'application_deadline', 'status']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

# --- VacancyApplication (Ariza) Serializers ---
class VacancyApplicationSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    vacancy = JobVacancySerializer(read_only=True)
    class Meta:
        model = VacancyApplication
        fields = '__all__'

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

    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)

class VacancyApplicationManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyApplication
        fields = ['status', 'notes']
