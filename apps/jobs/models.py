# apps/jobs/models.py

from django.db import models
from apps.users.models import User
from apps.workspaces.models import Workspace

# --- 1. LOYIHA MODELI ---
class Job(models.Model):
    """
    Umumiy loyiha. Faqat Admin tomonidan yaratiladi.
    Har bir Job o'zining Workspace'iga ega.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Faol'),
        ('CLOSED', 'Yopilgan'),
    )
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='job'
    )
    title = models.CharField(max_length=200, verbose_name="Loyiha nomi")
    description = models.TextField(verbose_name="Loyiha tavsifi")
    base_hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, 
        verbose_name="Standart soatbay stavka"
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

# --- 2. VAKANSIYA MODELI ---
class JobVacancy(models.Model):
    """
    Ma'lum bir loyiha (Job) uchun ochilgan ish o'rni (vakansiya).
    Staff tomonidan yaratiladi.
    """
    STATUS_CHOICES = (
        ('OPEN', 'Ochiq'),
        ('CLOSED', 'Yopilgan'),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='vacancies')
    title = models.CharField(max_length=200, verbose_name="Vakansiya sarlavhasi")
    description = models.TextField(verbose_name="Vakansiya tavsifi")
    requirements = models.TextField(verbose_name="Talablar")
    slots_available = models.PositiveIntegerField(default=1, verbose_name="Bo'sh o'rinlar soni")
    application_deadline = models.DateField(verbose_name="Ariza topshirishning oxirgi kuni")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_vacancies')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_vacancies'
        ordering = ['-created_at']
        verbose_name = "Vakansiya"
        verbose_name_plural = "Vakansiyalar"
    
    def __str__(self):
        return f"{self.title} ({self.job.title} loyihasi uchun)"

# --- 3. TALABANING ARIZASI MODELI ---
class VacancyApplication(models.Model):
    """
    Talabaning ma'lum bir vakansiyaga topshirgan arizasi.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Kutilmoqda'),
        ('REVIEWING', 'Ko\'rib chiqilmoqda'),
        ('ACCEPTED', 'Qabul qilingan'),
        ('REJECTED', 'Rad etilgan'),
    )
    vacancy = models.ForeignKey(JobVacancy, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vacancy_applications')
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True, verbose_name="Staff uchun izohlar")

    class Meta:
        db_table = 'vacancy_applications'
        unique_together = ('vacancy', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f"Ariza: {self.applicant.get_full_name()} -> {self.vacancy.title}"

