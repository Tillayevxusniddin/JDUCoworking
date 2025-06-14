from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Student, Recruiter, Staff

class UserSerializer(serializers.ModelSerializer):
    """Serializer for displaying User details"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'date_of_birth',
                  'user_type', 'is_active', 'photo', 'phone_number', 'created_at']
        read_only_fields = ['id', 'username', 'created_at']

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for Admin to create new users"""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name',
                  'date_of_birth', 'user_type', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Parollar mos kelmaydi")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        validated_data['username'] = validated_data['email']
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Automatically create profile based on user_type
        import time
        if user.user_type == 'STUDENT':
            Student.objects.create(user=user, student_id=f"STU-{user.id:04d}-{int(time.time())}")
        elif user.user_type == 'RECRUITER':
            Recruiter.objects.create(user=user)
        elif user.user_type == 'STAFF':
            Staff.objects.create(user=user)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating User details"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'date_of_birth', 'phone_number', 'photo', 'is_active']

class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for Student profile details"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'user', 'student_id', 'it_skills', 'semester', 'year_of_study',
                  'hire_date', 'bio', 'resume_file', 'jlpt', 'ielts', 'level_status',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'student_id', 'created_at', 'updated_at']

class StudentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Student profile"""
    class Meta:
        model = Student
        fields = ['it_skills', 'semester', 'year_of_study', 'hire_date', 'bio',
                  'resume_file', 'jlpt', 'ielts', 'level_status']

class RecruiterProfileSerializer(serializers.ModelSerializer):
    """Serializer for Recruiter profile details"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Recruiter
        fields = ['id', 'user', 'company_name', 'position', 'company_website',
                  'company_description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class RecruiterUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Recruiter profile"""
    class Meta:
        model = Recruiter
        fields = ['company_name', 'position', 'company_website', 'company_description']

class StaffProfileSerializer(serializers.ModelSerializer):
    """Serializer for Staff profile details"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Staff
        fields = ['id', 'user', 'position', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class StaffUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Staff profile"""
    class Meta:
        model = Staff
        fields = ['position']

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Email yoki parol noto'g'ri")
        if not user.is_active:
            raise serializers.ValidationError("Hisob bloklangan")
        data['user'] = user
        return data

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, min_length=8,
                                         style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Yangi parollar mos kelmaydi")
        return attrs