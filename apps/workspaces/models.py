# apps/workspaces/models.py

from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User

class Workspace(models.Model):
    name = models.CharField(max_length=200, verbose_name="Workspace name")
    description = models.TextField(blank=True, verbose_name="Workspace description")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_workspaces',
        verbose_name='Creator (Workspace Owner)'
    )
    is_active = models.BooleanField(default=True, verbose_name="Active Workspace")
    max_members = models.PositiveIntegerField(default=50, verbose_name="Max Members")
    class WorkspaceType(models.TextChoices):
        JOB_PROJECT = 'JOB_PROJECT', 'Job Project'
    workspace_type = models.CharField(
        max_length=20,
        choices=WorkspaceType.choices,
        default=WorkspaceType.JOB_PROJECT,
        verbose_name="Workspace Type"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        db_table = 'workspaces'
        ordering = ['-created_at']
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"

    def __str__(self):
        return self.name
    
    @property
    def active_members_count(self):
        return self.members.filter(is_active=True).count()
    
    @property
    def is_full(self):
        return self.active_members_count >= self.max_members
    
class WorkspaceMember(models.Model):
    MEMBER_ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('TEAMLEADER', 'Team Leader'),
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('RECRUITER', 'Recruiter'),
    ]
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="Workspace"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workspace_memberships',
        verbose_name="User"
    )
    role = models.CharField(
        max_length=20,
        choices=MEMBER_ROLE_CHOICES,
        verbose_name="Membership Role"
    )
    hourly_rate_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Personal Hourly Rate (if different from standard)",
        help_text="If this field is left blank, the standard rate will be used."
    )

    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Joined at")
    is_active = models.BooleanField(default=True, verbose_name="Active Member")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Last Activity")

    class Meta:
        db_table = 'workspace_members'
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'user'], 
                name='unique_workspace_membership')
        ]
        ordering = ['-joined_at']
        verbose_name = "Workspace Member"
        verbose_name_plural = "Workspace Members"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} -> {self.workspace.name}"
    
    def clean(self):
        if not self.pk and self.workspace.is_full:
            raise ValidationError("Workspace is full, new members cannot be added.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)