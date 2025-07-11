# apps/workspaces/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import WorkspaceMember
from apps.notifications.utils import create_notification

@receiver(post_save, sender=WorkspaceMember)
def notify_on_new_member(sender, instance, created, **kwargs):
    """
    Sends a notification when a new member is added to a workspace.
    `created` - indicates whether the object was newly created.
    """
    if created:
        workspace = instance.workspace
        actor = workspace.created_by 

        create_notification(
            recipient=instance.user,
            actor=actor,
            verb=f"You added '{workspace.name}' workspace.",
            message=f"Congratulations! You have been added to the '{workspace.name}' workspace.",
            action_object=workspace
        )

@receiver(post_delete, sender=WorkspaceMember)
def notify_on_member_removal(sender, instance, **kwargs):
    """
    Sends a notification when a member is removed from a workspace.
    """
    workspace = instance.workspace
    
    create_notification(
        recipient=instance.user,
        actor=None,
        verb=f"You have been removed from '{workspace.name}' workspace.",
        message=f"You have been removed from the '{workspace.name}' workspace.",
        action_object=workspace
    )