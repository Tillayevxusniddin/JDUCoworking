# apps/workspaces/models.py

from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User

class Workspace(models.Model):
    # Bu model o'zgarishsiz qoladi
    name = models.CharField(max_length=200, verbose_name="Ish Maydoni")
    description = models.TextField(blank=True, verbose_name="Tavsifi")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_workspaces',
        verbose_name='Yaratgan foydalanuvchi'
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol ish maydoni")
    max_members = models.PositiveIntegerField(default=50, verbose_name="Maksimal a'zolar soni")
    workspace_type = models.CharField(
        max_length=20,
        choices=[
            ('GENERAL', "General"),
            ('PROJECT', 'Project'),
            ('STUDY', 'Study'),
            ('MEETING', 'Meeting'),
        ],
        default='GENERAL',
        verbose_name="Ish maydoni turi"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    class Meta:
        db_table = 'workspaces'
        ordering = ['-created_at']
        verbose_name = "Ish Maydoni"
        verbose_name_plural = "Ish Maydonlari"
        
    def __str__(self):
        return self.name
    
    @property
    def active_members_count(self):
        return self.members.filter(is_active=True).count()
    
    @property
    def is_full(self):
        return self.active_members_count >= self.max_members
    
class WorkspaceMember(models.Model):
    # --- CHOICES'DAGI XATOLIK TO'G'IRLANDI ---
    MEMBER_ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('TEAMLEADER', 'Team Leader'),
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('RECRUITER', 'Recruiter'),
    ]
    # ----------------------------------------
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="Ish maydoni"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workspace_memberships',
        verbose_name="Foydalanuvchi"
    )
    role = models.CharField(
        max_length=20,
        choices=MEMBER_ROLE_CHOICES,
        verbose_name="A'zolik roli" 
        # `default` olib tashlandi, chunki endi avtomatik belgilanadi.
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")
    is_active = models.BooleanField(default=True, verbose_name="Faol a'zo")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="So'nggi faoliyat")

    class Meta:
        db_table = 'workspace_members'
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'user'], 
                name='unique_workspace_membership')
        ]
        ordering = ['-joined_at']
        verbose_name = "Ish Maydoni A'zosi"
        verbose_name_plural = "Ish Maydoni A'zolari"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} -> {self.workspace.name}"
    
    def clean(self):
        if not self.pk and self.workspace.is_full:
            raise ValidationError("Ish maydoni to'liq, yangi a'zolar qo'shib bo'lmaydi.")
            
    def save(self, *args, **kwargs):
        # Bu yerda clean'ni chaqirish shart emas, chunki serializer'da tekshiruv bor.
        super().save(*args, **kwargs)