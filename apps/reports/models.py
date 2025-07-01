from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User, Student
import datetime

def validate_student_user(user_id):
    user = User.objects.get(pk=user_id)
    if user.user_type != 'STUDENT':
        raise ValidationError("Only Student users are valid")


def validate_staff_user(user_id):
    user = User.objects.get(pk=user_id)
    if user.user_type not in ['STAFF', 'ADMIN']:
        raise ValidationError("Only Staff or Admin users are valid")
    


class DailyReport(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name='daily_reports',
        validators=[validate_student_user]
    )
    studentprofile = models.ForeignKey(
        Student, on_delete=models.CASCADE,
        related_name='daily_reports'
    )
    report_date = models.DateField(verbose_name="Hisobot sanasi")
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Ishlangan soat")
    work_description = models.TextField(verbose_name="Bajarilgan ish tavsifi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_reports'
        ordering = ['-report_date']
        unique_together = ['student', 'report_date']
        verbose_name = "Kunlik Hisobot"
        verbose_name_plural = "Kunlik Hisobotlar"

        def __str__(self):
            return f"{self.student.first_name}-{self.student.last_name} -> {self.report_date}"
        

class SalaryRecord(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Kutilmoqda'),
        ('APPROVED', 'Tasdiqlangan'),
        ('REJECTED', 'Rad etilgan'),
        ('PAID', 'To\'langan'),
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='salary_records',
        validators=[validate_student_user]
    )
    month = models.IntegerField(verbose_name="Oy")
    year = models.IntegerField(verbose_name="Yil")
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Jami soat")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Soatbay stavka")
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Umumiy summa")
    deduction_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="Ushlanma foizi (%)")
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ushlanma miqdori")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sof miqdor (qo'lga)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_salaries',
        validators=[validate_staff_user]
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'salary_records'
        ordering = ['-year', '-month']
        unique_together = ['student', 'month', 'year']
        verbose_name = "Oylik Maosh Hisobi"
        verbose_name_plural = "Oylik Maosh Hisoblari"

    def save(self, *args, **kwargs):
    # Hisob-kitoblarni avtomatik bajarish
        self.gross_amount = self.total_hours * self.hourly_rate
        self.deduction_amount = (self.gross_amount * self.deduction_percentage) / 100
        self.net_amount = self.gross_amount - self.deduction_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} uchun maosh - {self.year}/{self.month}"
    


class MonthlyReport(models.Model):
    STATUS_CHOICES = (
        ('GENERATED', 'Yaratilgan'),
        ('APPROVED', 'Tasdiqlangan'),
        ('REJECTED', 'Rad etilgan'),
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='monthly_reports',
        validators=[validate_student_user]
    )
    studentprofile = models.ForeignKey(
        Student, on_delete=models.CASCADE,
        related_name='monthly_reports'
    )
    salary = models.OneToOneField(
        SalaryRecord,
        on_delete=models.CASCADE,
        related_name='monthly_report'
    )
    month = models.IntegerField()
    year = models.IntegerField()
    file = models.FileField(upload_to='monthly_reports/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATED')
    managed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='managed_reports',
        validators=[validate_staff_user]
    )
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monthly_reports'
        ordering = ['-year', '-month']
        unique_together = ('student', 'year', 'month')
        verbose_name = "Oylik Hisobot"
        verbose_name_plural = "Oylik Hisobotlar"

    def __str__(self):
        return f"{self.student.first_name}-{self.student.last_name} uchun oylik hisobot - {self.year}/{self.month}"










