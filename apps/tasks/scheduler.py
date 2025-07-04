# apps/tasks/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .jobs import update_overdue_tasks
from apps.reports.jobs import generate_monthly_reports_and_salaries # <-- YANGI IMPORT

def start():
    """
    Rejalashtiruvchini ishga tushiradi va vazifalarni qo'shadi.
    Bu funksiya server ishga tushganda bir marta chaqiriladi.
    """
    scheduler = BackgroundScheduler()
    # Vazifalar haqidagi ma'lumotni saqlash uchun Django'ning ma'lumotlar bazasidan foydalanamiz
    scheduler.add_jobstore(DjangoJobStore(), "default")
    # `update_overdue_tasks` funksiyasini har kuni tunda (masalan, 00:01 da) ishga tushirish
    scheduler.add_job(
        update_overdue_tasks,
        trigger='cron',
        hour='0',
        minute='1',
        id='update_overdue_tasks_job',  # Vazifa uchun unikal ID
        replace_existing=True,
    )
    
    scheduler.add_job(
        generate_monthly_reports_and_salaries,
        trigger='cron',
        day='1',
        hour='2',
        minute='0',
        id='generate_monthly_reports_job',
        replace_existing=True,
    )
    print("Scheduler started...")
    scheduler.start()