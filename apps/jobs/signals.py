# apps/jobs/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job, VacancyApplication
from apps.workspaces.models import Workspace, WorkspaceMember

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
@receiver(post_save, sender=VacancyApplication)
def add_student_to_workspace_on_acceptance(sender, instance, created, **kwargs):
    if not created and instance.status == 'ACCEPTED':
        student = instance.applicant
        workspace = instance.vacancy.job.workspace
        
        is_member_already = WorkspaceMember.objects.filter(workspace=workspace, user=student).exists()
        if not is_member_already:
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=student,
                role='STUDENT'
            )
            print(f"SUCCESS: {student.get_full_name()} was added to {workspace.name}")

