# apps/reports/models.py

from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User # Faqat User modelini ishlatamiz
import datetime

def validate_student_user(user_id):
    """Bu funksiya faqat user_type='STUDENT' bo'lgan foydalanuvchilarni qabul qiladi."""
    user = User.objects.get(pk=user_id)
    if user.user_type != 'STUDENT':
        raise ValidationError("Faqat 'STUDENT' turidagi foydalanuvchilar tanlanishi mumkin.")

def validate_staff_user(user_id):
    """Bu funksiya faqat user_type='STAFF' yoki 'ADMIN' bo'lganlarni qabul qiladi."""
    user = User.objects.get(pk=user_id)
    if user.user_type not in ['STAFF', 'ADMIN']:
        raise ValidationError("Faqat 'STAFF' yoki 'ADMIN' turidagi foydalanuvchilar tanlanishi mumkin.")

class DailyReport(models.Model):
    """Har bir talabaning kunlik hisoboti uchun model."""
    # Qaysi student hisobot yozgani
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_reports', validators=[validate_student_user])
    # Hisobot sanasi
    report_date = models.DateField(verbose_name="Hisobot sanasi")
    # Shu kuni necha soat ishlagani
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Ishlangan soat")
    # Nima ish qilgani haqida tavsif
    work_description = models.TextField(verbose_name="Bajarilgan ish tavsifi")
    # Yaratilgan va yangilangan vaqtlar
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_reports'
        ordering = ['-report_date']
        unique_together = ('student', 'report_date') # Bitta student bir kunda faqat bitta hisobot yozishi mumkin
        verbose_name = "Kunlik Hisobot"
        verbose_name_plural = "Kunlik Hisobotlar"

    def __str__(self):
        return f"{self.student.get_full_name()} uchun hisobot - {self.report_date}"

class SalaryRecord(models.Model):
    """Har bir talabaning oylik maoshi haqidagi yozuv."""
    STATUS_CHOICES = (
        ('PENDING', 'Kutilmoqda'), # Maosh hisoblandi, lekin tasdiqlanmadi
        ('APPROVED', 'Tasdiqlangan'), # Staff maoshni tasdiqladi
        ('REJECTED', 'Rad etilgan'), # Staff maoshni rad etdi
        ('PAID', 'To\'langan'), # Maosh to'lab berildi
    )
    # Maosh kimga tegishli
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_records', validators=[validate_student_user])
    # Qaysi oy va yil uchun
    month = models.IntegerField(verbose_name="Oy")
    year = models.IntegerField(verbose_name="Yil")
    # Shu oyda jami necha soat ishladi
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Jami soat")
    # Talabaning soatbay stavkasi (bu avtomatik job'da belgilanadi)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Soatbay stavka")
    # Umumiy topgan puli (soat * stavka)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Umumiy summa")
    # Coworking ushlab qoladigan foiz
    deduction_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'), verbose_name="Ushlanma foizi (%)")
    # Ushlab qolinadigan summa (umumiy summaning 20%)
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ushlanma miqdori")
    # Qo'liga oladigan sof puli (Umumiy - Ushlanma)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sof miqdor (qo'lga)")
    # Maoshning holati
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    # Kim tomonidan tasdiqlangani
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_salaries', validators=[validate_staff_user])
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'salary_records'
        ordering = ['-year', '-month']
        unique_together = ('student', 'month', 'year') # Bitta student uchun bir oyda faqat bitta maosh yozuvi
        verbose_name = "Oylik Maosh Yozuvi"
        verbose_name_plural = "Oylik Maosh Yozuvlari"

    def save(self, *args, **kwargs):
        # Bu funksiya har safar saqlashdan oldin hisob-kitobni avtomatik bajaradi
        self.gross_amount = self.total_hours * self.hourly_rate
        self.deduction_amount = (self.gross_amount * self.deduction_percentage) / 100
        self.net_amount = self.gross_amount - self.deduction_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.get_full_name()} uchun maosh - {self.year}/{self.month}"
    
class MonthlyReport(models.Model):
    """Har oy yakunida generatsiya qilinadigan Excel-hisobot uchun model."""
    STATUS_CHOICES = (
        ('GENERATED', 'Yaratilgan'),
        ('APPROVED', 'Tasdiqlangan'),
        ('REJECTED', 'Rad etilgan'),
    )
    # Hisobot kimga tegishli
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_reports', validators=[validate_student_user])
    # Bu hisobot qaysi maosh yozuviga bog'liq
    salary = models.OneToOneField(SalaryRecord, on_delete=models.CASCADE, related_name='monthly_report')
    # Qaysi oy va yil uchun
    month = models.IntegerField()
    year = models.IntegerField()
    # Generatsiya qilingan Excel fayl
    file = models.FileField(upload_to='monthly_reports/%Y/%m/')
    # Hisobot holati
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATED')
    # Qaysi Staff/Admin tomonidan boshqarilgani
    managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_reports', validators=[validate_staff_user])
    # Agar rad etilsa, sababi
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monthly_reports'
        ordering = ['-year', '-month']
        unique_together = ('student', 'year', 'month') # Bitta student uchun bir oyda faqat bitta oylik hisobot
        verbose_name = "Oylik Hisobot"
        verbose_name_plural = "Oylik Hisobotlar"

    def __str__(self):
        return f"{self.student.get_full_name()} uchun oylik hisobot - {self.year}/{self.month}"