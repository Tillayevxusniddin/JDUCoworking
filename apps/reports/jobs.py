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
    Creates separate monthly reports and salaries for all students for the past month for each work area.
    """
    print(f"Generating monthly reports... {timezone.now()}")
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
        workspaces = Workspace.objects.filter(
            daily_reports__student=student,
            daily_reports__report_date__year=year,
            daily_reports__report_date__month=month
        ).distinct()

        for workspace in workspaces:
            if MonthlyReport.objects.filter(student=student, workspace=workspace, year=year, month=month).exists():
                print(f"This monthly report for {student.get_full_name()} in workspace '{workspace.name}' for {year}-{month} already exists. Skipping...")
                continue
            reports = DailyReport.objects.filter(student=student, workspace=workspace, report_date__year=year, report_date__month=month)
            total_hours = reports.aggregate(Sum('hours_worked'))['hours_worked__sum'] or Decimal('0.00')
            final_hourly_rate = Decimal('0.00')
            job = getattr(workspace, 'job', None) 
            
            if job:
                try:
                    member_record = WorkspaceMember.objects.get(user=student, workspace=workspace)
                    if member_record.hourly_rate_override is not None:
                        final_hourly_rate = member_record.hourly_rate_override
                    else:
                        final_hourly_rate = job.base_hourly_rate
                except WorkspaceMember.DoesNotExist:
                    final_hourly_rate = job.base_hourly_rate

            salary = SalaryRecord.objects.create(
                student=student,
                workspace=workspace,
                year=year,
                month=month,
                total_hours=total_hours,
                hourly_rate=final_hourly_rate
            )

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = f"{year}-{month} Report"
            headers = ["Date", "Hours Worked", "Work Description"]
            sheet.append(headers)
            for report in reports.order_by('report_date'):
                row = [report.report_date.strftime("%Y-%m-%d"), report.hours_worked, report.work_description]
                sheet.append(row)
            
            excel_file_in_memory = ContentFile(b'')
            workbook.save(excel_file_in_memory)

            file_name = f"{student.first_name.lower()}_{workspace.name.replace(' ', '_').lower()}_{year}-{month}.xlsx"
            monthly_report = MonthlyReport(
                student=student,
                workspace=workspace,
                salary=salary,
                year=year,
                month=month,
            )
            monthly_report.file.save(file_name, excel_file_in_memory, save=True)
            print(f"This monthly report for {student.get_full_name()} in workspace '{workspace.name}' for {year}-{month} has been created.")

            create_notification(
                recipient=student,
                actor=None,
                verb="Monthly report generated",
                message=f"Your report for {year}-{month} in workspace '{workspace.name}' is ready. Please check it.",
                action_object=monthly_report
            )

    print("Monthly report generation completed.")
