# apps/users/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
# Circular import'ning oldini olish uchun WorkspaceMember'ni signal ichida import qilamiz
from apps.workspaces.models import WorkspaceMember
# ✅ YANGI IMPORT
from apps.notifications.utils import create_notification

@receiver(post_save, sender=Student)
def sync_student_role_in_workspaces(sender, instance, **kwargs):
    """
    Student'ning `level_status` maydoni o'zgarganda, uning barcha
    Workspace'lardagi rolini sinxronlashtiradi va bildirishnoma yuboradi.
    """
    user = instance.user
    
    # Ma'lumotlar bazasiga murojaatni kamaytirish uchun eski holatni tekshirish
    # Bu signal faqat 'level_status' maydoni haqiqatdan o'zgarganda ishlashi uchun
    if 'update_fields' in kwargs and kwargs['update_fields'] and 'level_status' not in kwargs['update_fields']:
        return

    # Agar studentning level_status'i TEAMLEAD bo'lsa...
    if instance.level_status == 'TEAMLEAD':
        # ...uning workspace'lardagi rolini 'TEAMLEADER'ga o'zgartiramiz.
        updated_count = WorkspaceMember.objects.filter(user=user).exclude(role='TEAMLEADER').update(role='TEAMLEADER')
        # ✅ AGAR ROL HAQIQATDAN O'ZGARGAN BO'LSA, BILDIRISHNOMA YUBORAMIZ
        if updated_count > 0:
            create_notification(
                recipient=user,
                actor=None, # Bu o'zgarishni kim qilgani noaniq (admin yoki staff bo'lishi mumkin)
                verb="sizning darajangiz oshirildi",
                message="Tabriklaymiz! Sizning darajangiz 'Team Leader'ga ko'tarildi. Endi sizga yangi imkoniyatlar ochiladi.",
                action_object=instance # Student profili
            )
            
    # Agar studentning level_status'i SIMPLE bo'lsa...
    elif instance.level_status == 'SIMPLE':
        # ...uning workspace'lardagi rolini 'STUDENT'ga qaytaramiz.
        updated_count = WorkspaceMember.objects.filter(user=user).exclude(role='STUDENT').update(role='STUDENT')
        # ✅ AGAR ROL HAQIQATDAN O'ZGARGAN BO'LSA, BILDIRISHNOMA YUBORAMIZ
        if updated_count > 0:
            create_notification(
                recipient=user,
                actor=None,
                verb="sizning darajangiz o'zgartirildi",
                message="Sizning darajangiz 'Student'ga o'zgartirildi.",
                action_object=instance
            )