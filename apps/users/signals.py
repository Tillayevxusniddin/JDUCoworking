# apps/users/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
# Circular import'ning oldini olish uchun WorkspaceMember'ni signal ichida import qilamiz
from apps.workspaces.models import WorkspaceMember

@receiver(post_save, sender=Student)
def sync_student_role_in_workspaces(sender, instance, **kwargs):
    """
    Student'ning `level_status` maydoni o'zgarganda, uning barcha
    Workspace'lardagi rolini avtomatik tarzda sinxronlashtiradi.
    """
    user = instance.user
    
    # Agar studentning level_status'i TEAMLEAD bo'lsa...    
    if instance.level_status == 'TEAMLEAD':
        # ...uning workspace'lardagi rolini 'TEAMLEADER'ga o'zgartiramiz.
        WorkspaceMember.objects.filter(user=user).update(role='TEAMLEADER')
        
    # Agar studentning level_status'i SIMPLE bo'lsa...
    elif instance.level_status == 'SIMPLE':
        # ...uning workspace'lardagi rolini 'STUDENT'ga qaytaramiz.
        WorkspaceMember.objects.filter(user=user).update(role='STUDENT')