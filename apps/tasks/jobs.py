# apps/tasks/jobs.py

from django.utils import timezone
from apps.tasks.models import Task
from django.db.models import Q
from apps.notifications.utils import create_notification

def update_overdue_tasks():
    """Update overdue tasks to 'FAILED' status and notify the task creator."""
    now = timezone.now().date()
    
    overdue_tasks = Task.objects.filter(
        due_date__lt=now
    ).exclude(
        Q(status='COMPLETED') | Q(status='CANCELED') | Q(status='FAILED')
    ).select_related('created_by')

    if overdue_tasks.exists():
        for task in overdue_tasks:
            create_notification(
                recipient=task.created_by,
                actor=None,
                verb="Task overdue",
                message=f"The task '{task.title}' is overdue and has been marked as 'FAILED'.",
                action_object=task
            )

        updated_count = overdue_tasks.update(status='FAILED')
        print(f'Successfully updated {updated_count} overdue tasks to "FAILED".')
    else:
        print('No overdue tasks to update.')
