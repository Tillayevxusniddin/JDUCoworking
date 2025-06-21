# apps/users/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
# WorkspaceMember'ni signal ichida import qilamiz, circular import'ning oldini olish uchun
from apps.workspaces.models import WorkspaceMember 

@receiver(post_save, sender=Student)
def update_workspace_role_on_level_status_change(sender, instance, **kwargs):
    """
    Student'ning `level_status` o'zgarganda uning Workspace'dagi rolini yangilaydi.
    """
    user = instance.user
    
    # Agar Student'ning level_status 'TEAMLEAD' bo'lsa
    if instance.level_status == 'TEAMLEAD':
        # U a'zo bo'lgan barcha ish maydonlarida rolini 'MODERATOR'ga o'zgartiramiz
        WorkspaceMember.objects.filter(user=user).update(role='MODERATOR')
    # Agar Student 'TEAMLEAD'dan boshqa statusga o'tkazilsa (masalan, 'SIMPLE'ga)
    elif instance.level_status == 'SIMPLE':
         # U a'zo bo'lgan barcha ish maydonlarida rolini 'MEMBER'ga qaytaramiz.
         # Bu yerda workspace yaratuvchisi bo'lsa, rolini o'zgartirmaslik logikasini ham qo'shsa bo'ladi.
         # Hozircha sodda qoldiramiz.
        WorkspaceMember.objects.filter(user=user).update(role='MEMBER')