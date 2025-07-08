# apps/jobs/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job, VacancyApplication
from apps.workspaces.models import Workspace, WorkspaceMember
from django.db import transaction

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
    """
    Ariza statusi 'ACCEPTED'ga o'zgarganda quyidagi amallarni bajaradi:
    1. Talabani tegishli workspace'ga a'zo qilib qo'shadi.
    2. Vakansiyadagi bo'sh o'rinlar sonini kamaytiradi.
    3. Agar bo'sh o'rinlar qolmasa, vakansiyani yopadi.
    """
    # Faqat mavjud ariza 'ACCEPTED' statusini olganda ishlaydi
    if instance.status == 'ACCEPTED':
        vacancy = instance.vacancy
        student = instance.applicant
        workspace = vacancy.job.workspace

        # 1. Talabani workspace'ga a'zo qilib qo'shish
        # `get_or_create` metodi talaba allaqachon a'zo bo'lsa, uni qayta qo'shmaydi.
        # `created` o'zgaruvchisi talaba yangi qo'shilganini bildiradi.
        member, created_new_member = WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            user=student,
            defaults={'role': 'STUDENT'}
        )

        # Agar haqiqatan ham yangi a'zo qo'shilgan bo'lsa, vakansiyani yangilaymiz
        if created_new_member:
            print(f"SUCCESS: {student.get_full_name()} '{workspace.name}'ga qo'shildi.")

            # 2. Vakansiyadagi bo'sh o'rinlarni kamaytirish
            if vacancy.slots_available > 0:
                vacancy.slots_available -= 1
                
                # 3. Agar o'rinlar tugagan bo'lsa, vakansiyani yopish
                if vacancy.slots_available == 0:
                    vacancy.status = 'CLOSED'
                    print(f"INFO: Vakansiya '{vacancy.title}' to'lganligi uchun yopildi.")

                vacancy.save()
