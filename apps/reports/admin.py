# apps/reports/admin.py

from django.contrib import admin
from .models import DailyReport, MonthlyReport, SalaryRecord

@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'report_date', 'hours_worked', 'created_at')
    list_filter = ('report_date', 'student')
    search_fields = ('student__first_name', 'student__last_name', 'work_description')
    date_hierarchy = 'report_date'

@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'year', 'month', 'status', 'created_at')
    list_filter = ('status', 'year', 'month')
    search_fields = ('student__first_name', 'student__last_name')
    raw_id_fields = ('student', 'salary', 'managed_by')

@admin.register(SalaryRecord)
class SalaryRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'year', 'month', 'net_amount', 'status', 'paid_at')
    list_filter = ('status', 'year', 'month')
    search_fields = ('student__first_name', 'student__last_name')
    raw_id_fields = ('student', 'approved_by')


