# apps/reports/jobs.py

from django.utils import timezone
from django.db.models import Sum
from openpyxl import Workbook
from django.core.files.base import ContentFile
from decimal import Decimal

from apps.users.models import User
from .models import DailyReport, SalaryRecord, MonthlyReport
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.notifications.utils import create_notification

def generate_monthly_reports_and_salaries():
    """
    O'tgan oy uchun barcha talabalarning har bir ish maydonidagi faoliyati bo'yicha
    alohida oylik hisobotlar va maoshlarni yaratadi.
    """
    print(f"Oylik hisobotlarni generatsiya qilish boshlandi... {timezone.now()}")
    today = timezone.now().date()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timezone.timedelta(days=1)
    year = last_day_of_previous_month.year
    month = last_day_of_previous_month.month

    # O'tgan oyda hisobot yozgan barcha studentlarni topamiz
    students_with_reports = User.objects.filter(
        user_type='STUDENT',
        daily_reports__report_date__year=year,
        daily_reports__report_date__month=month
    ).distinct()

    for student in students_with_reports:
        # Studentning o'tgan oydagi barcha workspace'larini topamiz
        workspaces = Workspace.objects.filter(
            daily_reports__student=student,
            daily_reports__report_date__year=year,
            daily_reports__report_date__month=month
        ).distinct()

        # Har bir workspace uchun alohida hisobot yaratamiz
        for workspace in workspaces:
            if MonthlyReport.objects.filter(student=student, workspace=workspace, year=year, month=month).exists():
                print(f"{student.get_full_name()} uchun '{workspace.name}'dagi {year}-{month} hisoboti allaqachon mavjud.")
                continue

            # Faqat shu workspace uchun hisobotlarni olamiz
            reports = DailyReport.objects.filter(student=student, workspace=workspace, report_date__year=year, report_date__month=month)
            total_hours = reports.aggregate(Sum('hours_worked'))['hours_worked__sum'] or Decimal('0.00')
            
            final_hourly_rate = Decimal('0.00')
            
            # Workspace'ga bog'langan Job'ni to'g'ri related_name ('job') orqali olamiz
            job = getattr(workspace, 'job', None) 
            
            if job:
                try:
                    member_record = WorkspaceMember.objects.get(user=student, workspace=workspace)
                    # Agar shaxsiy stavka bo'lsa, o'shani olamiz
                    if member_record.hourly_rate_override is not None:
                        final_hourly_rate = member_record.hourly_rate_override
                    # Aks holda, Job'ning standart stavkasini olamiz
                    else:
                        final_hourly_rate = job.base_hourly_rate
                except WorkspaceMember.DoesNotExist:
                    # Agar a'zolik yozuvi topilmasa (ehtimoli kam), standart stavkani ishlatamiz
                    final_hourly_rate = job.base_hourly_rate
            
            # Maosh yozuvini yaratamiz
            salary = SalaryRecord.objects.create(
                student=student,
                workspace=workspace,
                year=year,
                month=month,
                total_hours=total_hours,
                hourly_rate=final_hourly_rate
            )

            # Excel fayl yaratamiz
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = f"{year}-{month} Hisobot"
            headers = ["Sana", "Ishlangan soat", "Bajarilgan ish tavsifi"]
            sheet.append(headers)
            for report in reports.order_by('report_date'):
                row = [report.report_date.strftime("%Y-%m-%d"), report.hours_worked, report.work_description]
                sheet.append(row)
            
            # Faylni xotiraga saqlaymiz
            excel_file_in_memory = ContentFile(b'')
            workbook.save(excel_file_in_memory)
            
            # Oylik hisobotni yaratib, faylni unga bog'laymiz
            file_name = f"{student.first_name.lower()}_{workspace.name.replace(' ', '_').lower()}_{year}-{month}.xlsx"
            monthly_report = MonthlyReport(
                student=student,
                workspace=workspace,
                salary=salary,
                year=year,
                month=month,
            )
            monthly_report.file.save(file_name, excel_file_in_memory, save=True)
            print(f"{student.get_full_name()} uchun '{workspace.name}'dagi {year}-{month} hisoboti va maoshi yaratildi.")

            # ✅ YANGI QO'SHIMCHA: TALABAGA HISOBOT TAYYORLIGI HAQIDA BILDIRISHNOMA
            create_notification(
                recipient=student,
                actor=None, # Tizim tomonidan
                verb="uchun oylik hisobot generatsiya qilindi",
                message=f"Sizning {year}-{month} oyi uchun '{workspace.name}' ish maydonidagi hisobotingiz tayyor. Iltimos, tekshirib chiqing.",
                action_object=monthly_report
            )
    
    print("Oylik hisobotlarni generatsiya qilish tugadi.")
