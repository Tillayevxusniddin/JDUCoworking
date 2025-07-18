# apps/notifications/utils.py (yangi fayl yarating)

from django.contrib.contenttypes.models import ContentType
from .models import Notification

def create_notification(recipient, actor, verb, message, action_object=None, target=None):
    """
    Create a new notification.
    """
    if recipient == actor:
        return

    notification = Notification(
        recipient=recipient,
        actor=actor,
        verb=verb,
        message=message,
    )
    if action_object:
        notification.action_object = action_object
    if target:
        notification.target = target
    
    notification.save()