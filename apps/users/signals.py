# apps/users/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
from apps.workspaces.models import WorkspaceMember
from apps.notifications.utils import create_notification

@receiver(post_save, sender=Student)
def sync_student_role_in_workspaces(sender, instance, **kwargs):
    """
    Syncs the student's role in all workspaces based on their level status.
    If the student's level_status is 'TEAMLEAD', their role in all workspaces is set to 'TEAMLEADER'.
    If the student's level_status is 'SIMPLE', their role in all workspaces is set to 'STUDENT'.
    This function is triggered after a Student instance is saved.
    """
    user = instance.user
    
    if 'update_fields' in kwargs and kwargs['update_fields'] and 'level_status' not in kwargs['update_fields']:
        return
    if instance.level_status == 'TEAMLEAD':
        updated_count = WorkspaceMember.objects.filter(user=user).exclude(role='TEAMLEADER').update(role='TEAMLEADER')
        if updated_count > 0:
            create_notification(
                recipient=user,
                actor=None, 
                verb="Your level has been upgraded",
                message="Congratulations! Your level has been upgraded to 'Team Leader'. New opportunities await you.",
                action_object=instance
            )
    elif instance.level_status == 'SIMPLE':
        updated_count = WorkspaceMember.objects.filter(user=user).exclude(role='STUDENT').update(role='STUDENT')
        if updated_count > 0:
            create_notification(
                recipient=user,
                actor=None,
                verb="Your level has been downgraded",
                message="Your level has been downgraded to 'Student'.",
                action_object=instance
            )