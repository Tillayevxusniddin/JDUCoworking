# apps/jobs/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job, VacancyApplication
from apps.workspaces.models import Workspace, WorkspaceMember
from django.db import transaction
from apps.notifications.utils import create_notification

@receiver(post_save, sender=Job)
def create_workspace_for_job(sender, instance, created, **kwargs):
    if created and not instance.workspace:
        workspace = Workspace.objects.create(
            name=f"{instance.title} Project",
            description=f"Automatically created workspace for portfolio project'{instance.title}'",
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

@receiver(post_save, sender=VacancyApplication)
@transaction.atomic
def handle_accepted_application(sender, instance, **kwargs):
    if instance.status == 'ACCEPTED':
        vacancy = instance.vacancy
        student = instance.applicant
        workspace = vacancy.job.workspace

        member, created_new_member = WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            user=student,
            defaults={'role': 'STUDENT'}
        )
    
        if created_new_member:
            print(f"SUCCESS: {student.get_full_name()} added to '{workspace.name}'.")
            reviewer = getattr(instance, '_reviewed_by_user', vacancy.created_by)
            
            create_notification(
                recipient=student,
                actor=reviewer,
                verb=f"Your application has been approved",
                message=f"Congratulations! Your application for the '{vacancy.title}' vacancy has been accepted and you have been added to the '{workspace.name}' workspace.",
                action_object=instance,
                target=workspace
            )

            if vacancy.slots_available > 0:
                vacancy.slots_available -= 1
                if vacancy.slots_available == 0:
                    vacancy.status = 'CLOSED'
                    print(f"INFO: Vacancy '{vacancy.title}' is now closed.")
                vacancy.save(update_fields=['slots_available', 'status'])