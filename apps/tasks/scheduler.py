# apps/tasks/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .jobs import update_overdue_tasks
from apps.reports.jobs import generate_monthly_reports_and_salaries

def start():
    """
    Start the background scheduler to run periodic tasks.
    This function initializes the scheduler and adds jobs to it.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        update_overdue_tasks,
        trigger='cron',
        hour='0',
        minute='1',
        id='update_overdue_tasks_job', 
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