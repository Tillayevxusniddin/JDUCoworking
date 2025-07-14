# apps/users/signals.py

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# Models from this app
from .models import User, Student

# Models and utils from other apps
from apps.workspaces.models import WorkspaceMember
from apps.notifications.utils import create_notification

# ====================================================================
# SIGNAL 1: Send a welcome email when a new User is created.
# ====================================================================
@receiver(post_save, sender=User)
def send_welcome_email_on_user_create(sender, instance, created, **kwargs):
    """
    Sends a welcome email via AWS Lambda when a new user is created.
    """
    if created:
        print(f"New user created: {instance.email}. Triggering welcome email.")

        lambda_url = settings.LAMBDA_WELCOME_EMAIL_URL
        api_key = settings.LAMBDA_API_KEY

        if not lambda_url or not api_key:
            print("Warning: Lambda URL or API Key is not configured. Skipping email.")
            return

        payload = {
            "email": instance.email,
            "first_name": instance.first_name
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }

        try:
            response = requests.post(lambda_url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"Successfully triggered welcome email for {instance.email}. Lambda response: {response.json()}")
            else:
                print(f"Error triggering Lambda for {instance.email}. Status: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to Lambda endpoint: {e}")

# ====================================================================
# SIGNAL 2: Sync student's role in workspaces when their level changes.
# ====================================================================
@receiver(post_save, sender=Student)
def sync_student_role_in_workspaces(sender, instance, **kwargs):
    """
    Syncs the student's role in all workspaces based on their level status
    and sends a notification.
    """
    user = instance.user
    
    # This signal should only run if the 'level_status' field was actually updated
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
                verb="Your level has been changed",
                message="Your level has been set to 'Student'.",
                action_object=instance
            )
