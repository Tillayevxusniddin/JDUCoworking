# apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Student, Recruiter, Staff
import time

# --- Y A N G I   S E R I A L I Z E R ---
class LogoutSerializer(serializers.Serializer):
    """Logout uchun refresh tokenni qabul qiluvchi serializer."""
    refresh = serializers.CharField()
# ----------------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'date_of_birth',
                  'user_type', 'is_active', 'photo', 'phone_number', 'created_at']
        read_only_fields = ['id', 'username', 'created_at', 'user_type']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name',
                  'date_of_birth', 'user_type', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Parollar mos kelmaydi."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        validated_data['username'] = validated_data['email']
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user.user_type == 'STUDENT':
            student_id = f"STU-{user.id:04d}-{int(time.time())}"
            Student.objects.create(user=user, student_id=student_id)
        elif user.user_type == 'RECRUITER':
            Recruiter.objects.create(user=user)
        elif user.user_type == 'STAFF':
            Staff.objects.create(user=user)
            
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'date_of_birth', 'phone_number', 'photo', 'is_active']
        extra_kwargs = {
            'is_active': {'help_text': 'Foydalanuvchi hisobining faolligi (faqat Admin o`zgartira oladi).'}
        }

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    level_status_display = serializers.CharField(source='get_level_status_display', read_only=True)
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['id', 'user', 'student_id', 'created_at', 'updated_at', 'level_status_display']

class StudentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['it_skills', 'semester', 'year_of_study', 'hire_date', 'bio',
                  'resume_file', 'jlpt', 'ielts', 'level_status']

class RecruiterProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Recruiter
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class RecruiterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruiter
        fields = ['company_name', 'position', 'company_website', 'company_description']

class StaffProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Staff
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class StaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['position']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Email yoki parol noto'g'ri")
        if not user.is_active:
            raise serializers.ValidationError("Bu hisob faol emas")
        data['user'] = user
        return data

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Yangi parollar mos kelmadi"})
        return attrs