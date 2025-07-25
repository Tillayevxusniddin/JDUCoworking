# apps/users/serializers.py

import json
from rest_framework import serializers
import requests
from django.conf import settings
from django.contrib.auth import authenticate
from .models import User, Student, Recruiter, Staff
from apps.workspaces.models import WorkspaceMember
from apps.notifications.utils import create_notification

class StringifiedJSONField(serializers.JSONField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                self.fail('invalid', input=data)
        return super().to_internal_value(data)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "New passwords do not match"})
        return attrs

# --- USER SERIALIZERS ---
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password', 'groups', 'user_permissions', 'last_login')

class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'user_type']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'user_type', 'phone_number']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if user.user_type == 'STUDENT': Student.objects.create(user=user)
        elif user.user_type == 'RECRUITER': Recruiter.objects.create(user=user)
        elif user.user_type == 'STAFF': Staff.objects.create(user=user)
        create_notification(
            recipient=user, actor=None, verb="You have successfully registered on JDU Coworking platform.",
            message=f"Welcome, {user.first_name}! You have successfully registered on JDU Coworking platform."
        )
    
        print(f"New user created: {user.email}. Triggering welcome email.")
        lambda_url = settings.LAMBDA_WELCOME_EMAIL_URL
        api_key = settings.LAMBDA_API_KEY

        if not lambda_url or not api_key:
            print("Warning: Lambda URL or API Key is not configured. Skipping email.")
        else:
            payload = {
                "email": user.email,
                "first_name": user.first_name,
                "password": password  
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key
            }
            try:
                response = requests.post(lambda_url, json=payload, headers=headers, timeout=5)
                if response.status_code == 200:
                    print(f"Successfully triggered welcome email for {user.email}.")
                else:
                    print(f"Error triggering Lambda for {user.email}. Status: {response.status_code}, Response: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to connect to Lambda endpoint: {e}")
        return user

       

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'user_type', 'date_of_birth', 'phone_number', 'photo', 'is_active']
    def update(self, instance, validated_data):
        old_user_type = instance.user_type
        new_user_type = validated_data.get('user_type', old_user_type)
        if old_user_type != new_user_type:
            if hasattr(instance, 'student_profile'): instance.student_profile.delete()
            elif hasattr(instance, 'recruiter_profile'): instance.recruiter_profile.delete()
            elif hasattr(instance, 'staff_profile'): instance.staff_profile.delete()
            if new_user_type == 'STUDENT': Student.objects.create(user=instance)
            elif new_user_type == 'RECRUITER': Recruiter.objects.create(user=instance)
            elif new_user_type == 'STAFF': Staff.objects.create(user=instance)
            new_role_map = {'STUDENT': 'STUDENT', 'STAFF': 'STAFF', 'RECRUITER': 'RECRUITER', 'ADMIN': 'ADMIN'}
            new_role = new_role_map.get(new_user_type)
            if new_role:
                if new_role == 'STUDENT' and hasattr(instance, 'student_profile') and instance.student_profile.level_status == 'TEAMLEAD':
                    new_role = 'TEAMLEADER'
                WorkspaceMember.objects.filter(user=instance).update(role=new_role)
        return super().update(instance, validated_data)

# --- PROFILE SERIALIZERS ---
class StudentProfileListSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    class Meta:
        model = Student
        fields = ['id', 'user', 'level_status', 'year_of_study']

class StudentProfileDetailSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    class Meta:
        model = Student
        fields = '__all__'

class RecruiterProfileListSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    class Meta:
        model = Recruiter
        fields = ['id', 'user', 'company_name', 'position']

class RecruiterProfileDetailSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    class Meta:
        model = Recruiter
        fields = '__all__'

class StaffProfileListSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    class Meta:
        model = Staff
        fields = ['id', 'user', 'position']

class StaffProfileDetailSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    class Meta:
        model = Staff
        fields = '__all__'

# --- PROFILE UPDATE SERIALIZERS ---
class StudentProfilePersonalUpdateSerializer(serializers.ModelSerializer):
    it_skills = StringifiedJSONField(required=False)
    class Meta:
        model = Student
        fields = ['it_skills', 'bio', 'resume_file', 'jlpt', 'ielts']

class StudentProfileAdminUpdateSerializer(serializers.ModelSerializer):
    it_skills = StringifiedJSONField(required=False)
    class Meta:
        model = Student
        exclude = ['user']

class RecruiterProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruiter
        fields = ['company_name', 'position', 'company_website', 'company_description']

class StaffProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['position']
