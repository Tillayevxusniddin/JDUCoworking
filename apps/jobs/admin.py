# apps/jobs/admin.py
from django.contrib import admin
from .models import Job, JobVacancy, VacancyApplication

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'workspace')
    list_filter = ('status',)
    search_fields = ('title', 'description')
    raw_id_fields = ('created_by', 'workspace')
    readonly_fields = ('workspace',)

@admin.register(JobVacancy)
class JobVacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'job', 'status', 'application_deadline', 'slots_available')
    list_filter = ('status', 'job')
    search_fields = ('title', 'job__title')
    raw_id_fields = ('job', 'created_by')

@admin.register(VacancyApplication)
class VacancyApplicationAdmin(admin.ModelAdmin):
    list_display = ('vacancy', 'applicant', 'status', 'applied_at')
    list_filter = ('status', 'vacancy__job')
    search_fields = ('applicant__first_name', 'applicant__last_name', 'vacancy__title')
    raw_id_fields = ('vacancy', 'applicant')
