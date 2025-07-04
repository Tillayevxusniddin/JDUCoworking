# apps/users/serializers.py

import json
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Student, Recruiter, Staff
from apps.workspaces.models import WorkspaceMember
import time

class StringifiedJSONField(serializers.JSONField):
    """
    Matn (string) ko'rinishida kelgan JSON'ni to'g'ri qabul qilib,
    Python obyektiga (list/dict) o'girib beradigan maxsus maydon.
    Bu aynan multipart/form-data bilan ishlash uchun kerak.
    """
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                # Matnni JSON sifatida o'qiymiz
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                self.fail('invalid', input=data)
        # Agar ma'lumot allaqachon JSON bo'lsa (masalan, raw/json so'rovdan)
        # uni standart usulda qayta ishlaymiz.
        return super().to_internal_value(data)

# --- AUTH SERIALIZER'LARI ---
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})
    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError("Email yoki parol noto'g'ri yoki hisob faol emas.")
        data['user'] = user
        return data

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Yangi parollar mos kelmadi"})
        return attrs

# --- USER MANAGEMENT SERIALIZER'LARI ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password', 'groups', 'user_permissions', 'last_login')

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
        
        # Foydalanuvchi turiga qarab profil yaratish
        if user.user_type == 'STUDENT':
            Student.objects.create(user=user)
        elif user.user_type == 'RECRUITER':
            Recruiter.objects.create(user=user)
        elif user.user_type == 'STAFF':
            Staff.objects.create(user=user)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'user_type',
            'date_of_birth', 
            'phone_number', 
            'photo', 
            'is_active'
        ]

    def update(self, instance, validated_data):
        """
        User'ning user_type o'zgarganda eski profilni o'chirib, yangisini yaratadi
        va workspace'dagi rollarini yangilaydi.
        """
        old_user_type = instance.user_type
        new_user_type = validated_data.get('user_type', old_user_type)

        # Agar user_type o'zgargan bo'lsa...
        if old_user_type != new_user_type:
            # 1. Eski profilni topib o'chiramiz
            if old_user_type == 'STUDENT' and hasattr(instance, 'student_profile'):
                instance.student_profile.delete()
            elif old_user_type == 'RECRUITER' and hasattr(instance, 'recruiter_profile'):
                instance.recruiter_profile.delete()
            elif old_user_type == 'STAFF' and hasattr(instance, 'staff_profile'):
                instance.staff_profile.delete()

            # 2. Yangi profilni yaratamiz
            if new_user_type == 'STUDENT':
                Student.objects.create(user=instance)
            elif new_user_type == 'RECRUITER':
                Recruiter.objects.create(user=instance)
            elif new_user_type == 'STAFF':
                Staff.objects.create(user=instance)

            # 3. Workspace'lardagi rolini yangilash
            new_role_map = {
                'STUDENT': 'STUDENT',
                'STAFF': 'STAFF',
                'RECRUITER': 'RECRUITER',
                'ADMIN': 'ADMIN',
            }
            new_role = new_role_map.get(new_user_type)
            if new_role:
                # Agar student TEAMLEAD bo'lgan bo'lsa, uni oddiy STUDENT'ga aylantiramiz
                # Chunki user_type o'zgardi. Yangi turda TEAMLEAD statusi bo'lmasligi mumkin.
                if new_role == 'STUDENT' and hasattr(instance, 'student_profile'):
                    if instance.student_profile.level_status == 'TEAMLEAD':
                         new_role = 'TEAMLEADER'

                WorkspaceMember.objects.filter(user=instance).update(role=new_role)

        # Ota-klassning update metodini chaqirib, qolgan maydonlarni yangilaymiz
        return super().update(instance, validated_data)


# --- STUDENT PROFILE SERIALIZER'LARI ---

class StudentProfileSerializer(serializers.ModelSerializer):
    """Talaba profilini KO'RISH uchun serializer (barcha maydonlar)."""
    user = UserSerializer(read_only=True)
    class Meta:
        model = Student
        fields = '__all__'

class StudentProfilePersonalUpdateSerializer(serializers.ModelSerializer):
    """Talabaning O'ZI profilini tahrirlashi uchun (cheklangan maydonlar)."""
    
    # Oddiy JSONField o'rniga o'zimiz yaratgan maxsus maydonni ishlatamiz
    it_skills = StringifiedJSONField(required=False)

    class Meta:
        model = Student
        fields = ['it_skills', 'bio', 'resume_file', 'jlpt', 'ielts']

class StudentProfileAdminUpdateSerializer(serializers.ModelSerializer):
    """ADMIN yoki STAFF tomonidan talaba profilini tahrirlash uchun (barcha maydonlar)."""
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['user', 'student_id'] # Userni o'zgartirib bo'lmaydi


# --- RECRUITER PROFILE SERIALIZER'LARI ---

class RecruiterProfileSerializer(serializers.ModelSerializer):
    """Ishga oluvchi profilini KO'RISH uchun serializer."""
    user = UserSerializer(read_only=True)
    class Meta:
        model = Recruiter
        fields = '__all__'

class RecruiterProfileUpdateSerializer(serializers.ModelSerializer):
    """RECRUITER yoki ADMIN tomonidan profilni tahrirlash uchun."""
    class Meta:
        model = Recruiter
        fields = ['company_name', 'position', 'company_website', 'company_description']


# --- STAFF PROFILE SERIALIZER'LARI ---

class StaffProfileSerializer(serializers.ModelSerializer):
    """Xodim profilini KO'RISH uchun serializer."""
    user = UserSerializer(read_only=True)
    class Meta:
        model = Staff
        fields = '__all__'

class StaffProfileUpdateSerializer(serializers.ModelSerializer):
    """STAFF yoki ADMIN tomonidan profilni tahrirlash uchun."""
    class Meta:
        model = Staff
        fields = ['position']