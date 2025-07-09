# apps/jobs/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job, VacancyApplication
from apps.workspaces.models import Workspace, WorkspaceMember
from django.db import transaction
from apps.notifications.utils import create_notification


# 1-Signal: Job yaratilganda Workspace yaratish
@receiver(post_save, sender=Job)
def create_workspace_for_job(sender, instance, created, **kwargs):
    if created and not instance.workspace:
        workspace = Workspace.objects.create(
            name=f"{instance.title} Loyihasi",
            description=f"'{instance.title}' loyihasi uchun avtomatik yaratilgan ish maydoni.",
            created_by=instance.created_by,
            workspace_type='JOB_PROJECT'
        )
        instance.workspace = workspace
        instance.save()
        
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=instance.created_by,
            role='ADMIN'
        )

# 2-Signal: Ariza tasdiqlanganda talabani workspace'ga qo'shish
# 2-Signal: Ariza tasdiqlanganda barcha kerakli amallarni bajarish (YANGILANGAN)
@receiver(post_save, sender=VacancyApplication)
@transaction.atomic
def handle_accepted_application(sender, instance, **kwargs):
    # Bu signal faqat 'ACCEPTED' statusi uchun ishlashi kerak
    if instance.status == 'ACCEPTED':
        vacancy = instance.vacancy
        student = instance.applicant
        workspace = vacancy.job.workspace

        member, created_new_member = WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            user=student,
            defaults={'role': 'STUDENT'}
        )
        
        # Faqatgina haqiqatdan ham YENGI a'zo qo'shilgan bo'lsa, qolgan amallarni bajaramiz.
        # Bu ariza qayta-qayta 'ACCEPTED' qilinishining oldini oladi.
        if created_new_member:
            print(f"SUCCESS: {student.get_full_name()} '{workspace.name}'ga qo'shildi.")

            # ✅ TUZATILGAN QISM: `actor`ni `view`dan kelgan foydalanuvchi bilan almashtiramiz
            # `reviewed_by` degan atribut modelda yo'q, uni `view`da qo'lda qo'shib qo'yamiz
            reviewer = getattr(instance, '_reviewed_by_user', vacancy.created_by)
            
            create_notification(
                recipient=student,
                actor=reviewer,
                verb=f"arizangizni tasdiqladi",
                message=f"Tabriklaymiz! Sizning '{vacancy.title}' vakansiyasiga arizangiz qabul qilindi va siz '{workspace.name}' ish maydoniga qo'shildingiz.",
                action_object=instance,
                target=workspace
            )

            if vacancy.slots_available > 0:
                vacancy.slots_available -= 1
                if vacancy.slots_available == 0:
                    vacancy.status = 'CLOSED'
                    print(f"INFO: Vakansiya '{vacancy.title}' to'lganligi uchun yopildi.")
                vacancy.save(update_fields=['slots_available', 'status'])