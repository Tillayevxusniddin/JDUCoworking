# apps/workspaces/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import WorkspaceMember
from apps.notifications.utils import create_notification

@receiver(post_save, sender=WorkspaceMember)
def notify_on_new_member(sender, instance, created, **kwargs):
    """
    Ish maydoniga yangi a'zo qo'shilganda bildirishnoma yuboradi.
    `created` - bu obyekt yangi yaratilganini bildiradi.
    """
    if created:
        workspace = instance.workspace
        # Harakatni bajargan adminni topish qiyinroq bo'lgani uchun `actor`ni `None` qoldiramiz
        # yoki workspace yaratuvchisini ko'rsatishimiz mumkin.
        actor = workspace.created_by 

        create_notification(
            recipient=instance.user,
            actor=actor,
            verb=f"sizni '{workspace.name}' ish maydoniga qo'shdi",
            message=f"Tabriklaymiz! Siz '{workspace.name}' ish maydoniga a'zo sifatida qo'shildingiz.",
            action_object=workspace
        )

@receiver(post_delete, sender=WorkspaceMember)
def notify_on_member_removal(sender, instance, **kwargs):
    """
    Ish maydonidan a'zo o'chirilganda bildirishnoma yuboradi.
    """
    workspace = instance.workspace
    
    create_notification(
        recipient=instance.user,
        # Bu yerda ham actor noaniq, chunki o'chirgan adminni signal orqali bilib bo'lmaydi
        actor=None, 
        verb=f"'{workspace.name}' ish maydonidan chiqarildingiz",
        message=f"Siz '{workspace.name}' ish maydonidagi a'zolikdan chiqarildingiz.",
        action_object=workspace
    )