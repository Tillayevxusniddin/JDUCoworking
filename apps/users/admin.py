from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Recruiter, Staff

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'date_of_birth', 'photo', 'phone_number')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('email', 'first_name', 'last_name', 'user_type',
                                        'date_of_birth', 'phone_number')}),
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'level_status', 'semester', 'year_of_study']
    list_filter = ['level_status', 'semester', 'year_of_study']
    search_fields = ['user__email', 'student_id']
    raw_id_fields = ['user']

@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'position']
    list_filter = ['company_name']
    search_fields = ['user__email', 'company_name']
    raw_id_fields = ['user']

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'position']
    list_filter = ['position']
    search_fields = ['user__email', 'position']
    raw_id_fields = ['user']