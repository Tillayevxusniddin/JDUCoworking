# apps/jobs/models.py

from django.db import models
from apps.users.models import User
from apps.workspaces.models import Workspace

class Job(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
    )
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='job'
    )
    title = models.CharField(max_length=200, verbose_name="Project title")
    description = models.TextField(verbose_name="Project description")
    base_hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, 
        verbose_name="Standard hourly rate"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']
        verbose_name = "Loyiha (Job)"
        verbose_name_plural = "Loyihalar (Jobs)"

    def __str__(self):
        return self.title

class JobVacancy(models.Model):

    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='vacancies')
    title = models.CharField(max_length=200, verbose_name="Vacancy title")
    description = models.TextField(verbose_name="Vacancy description")
    requirements = models.TextField(verbose_name="Requirements")
    slots_available = models.PositiveIntegerField(default=1, verbose_name="Available slots")
    application_deadline = models.DateField(verbose_name="Application deadline")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_vacancies')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_vacancies'
        ordering = ['-created_at']
        verbose_name = "Vacancy"
        verbose_name_plural = "Vacancies"

    def __str__(self):
        return f"{self.title} ({self.job.title} project)"


class VacancyApplication(models.Model):
    """
    Applicant's application for a specific vacancy.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('REVIEWING', 'Reviewing'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )
    vacancy = models.ForeignKey(JobVacancy, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vacancy_applications')
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True, verbose_name="Staff notes")

    class Meta:
        db_table = 'vacancy_applications'
        unique_together = ('vacancy', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f"Ariza: {self.applicant.get_full_name()} -> {self.vacancy.title}"

