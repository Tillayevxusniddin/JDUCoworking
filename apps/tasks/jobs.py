# apps/tasks/jobs.py

from django.utils import timezone
from apps.tasks.models import Task
from django.db.models import Q
from apps.notifications.utils import create_notification

def update_overdue_tasks():
    """Muddati o'tgan vazifalarni topib, statusini 'FAILED' ga o'zgartiradi va bildirishnoma yuboradi."""
    now = timezone.now().date()
    
    overdue_tasks = Task.objects.filter(
        due_date__lt=now
    ).exclude(
        Q(status='COMPLETED') | Q(status='CANCELED') | Q(status='FAILED')
    ).select_related('created_by') # ✅ `created_by`ni oldindan yuklab olamiz

    if overdue_tasks.exists():
        # ✅ BILDIRISHNOMA YUBORISH
        for task in overdue_tasks:
            create_notification(
                recipient=task.created_by,
                actor=None, # Tizim tomonidan
                verb="siz yaratgan vazifaning muddati o'tib ketdi",
                message=f"DIQQAT: Siz yaratgan '{task.title}' nomli vazifaning muddati o'tib ketganligi uchun 'Bajarilmadi' (Failed) deb belgilandi.",
                action_object=task
            )

        updated_count = overdue_tasks.update(status='FAILED')
        print(f'Successfully updated {updated_count} overdue tasks to "FAILED".')
    else:
        print('No overdue tasks to update.')
