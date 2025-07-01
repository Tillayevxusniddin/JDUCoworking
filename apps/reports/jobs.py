# apps/reports/jobs.py

from datetime import date
from django.utils import timezone
from django.db.models import Sum
from openpyxl import Workbook
from django.core.files.base import ContentFile

from apps.users.models import User
from .models import DailyReport, SalaryRecord, MonthlyReport

def generate_monthly_reports_and_salaries():
    """
    O'tgan oy uchun barcha talabalarning oylik hisobotlari va maoshlarini yaratadi.
    Har oyning 1-kuni ishga tushiriladi.
    """
    print(f"Oylik hisobotlarni generatsiya qilish boshlandi... {timezone.now()}")
    today = timezone.now().date()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timezone.timedelta(days=1)
    year = last_day_of_previous_month.year
    month = last_day_of_previous_month.month

    students_with_reports = User.objects.filter(
        user_type='STUDENT',
        daily_reports__report_date__year=year,
        daily_reports__report_date__month=month
    ).distinct()

    for student in students_with_reports:
        if MonthlyReport.objects.filter(student=student, year=year, month=month).exists():
            print(f"{student.get_full_name()} uchun {year}-{month} hisoboti allaqachon mavjud.")
            continue

        reports = DailyReport.objects.filter(student=student, report_date__year=year, report_date__month=month)
        total_hours = reports.aggregate(Sum('hours_worked'))['hours_worked__sum'] or 0
        
        # TODO: Soatbay stavkani har bir student uchun alohida modeldan olish kerak.
        # Hozircha statik qiymat ishlatamiz.
        hourly_rate = 10  # Misol: soatiga $10

        salary = SalaryRecord.objects.create(
            student=student,
            year=year,
            month=month,
            total_hours=total_hours,
            hourly_rate=hourly_rate
        )

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = f"{year}-{month} Hisobot"
        headers = ["Sana", "Ishlangan soat", "Bajarilgan ish tavsifi"]
        sheet.append(headers)
        for report in reports.order_by('report_date'):
            row = [report.report_date.strftime("%Y-%m-%d"), report.hours_worked, report.work_description]
            sheet.append(row)
        
        excel_file_in_memory = ContentFile(b'')
        workbook.save(excel_file_in_memory)
        
        file_name = f"{student.first_name.lower()}_{year}-{month}_report.xlsx"
        monthly_report = MonthlyReport(
            student=student,
            salary=salary,
            year=year,
            month=month,
        )
        monthly_report.file.save(file_name, excel_file_in_memory, save=True)
        
        print(f"{student.get_full_name()} uchun {year}-{month} hisoboti va maoshi muvaffaqiyatli yaratildi.")
    
    print("Oylik hisobotlarni generatsiya qilish tugadi.")