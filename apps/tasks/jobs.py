# apps/tasks/jobs.py

from django.utils import timezone
from apps.tasks.models import Task
from django.db.models import Q

def update_overdue_tasks():
    """Muddati o'tgan vazifalarni topib, statusini 'FAILED' ga o'zgartiradi."""
    now = timezone.now().date()
    
    # Tugatilmagan, bekor qilinmagan va muddati o'tgan vazifalarni topish
    overdue_tasks = Task.objects.filter(
        due_date__lt=now
    ).exclude(
        Q(status='COMPLETED') | Q(status='CANCELED') | Q(status='FAILED')
    )
    
    count = overdue_tasks.count()
    if count > 0:
        updated_count = overdue_tasks.update(status='FAILED')
        print(f'Successfully updated {updated_count} overdue tasks to "FAILED".')
    else:
        print('No overdue tasks to update.')