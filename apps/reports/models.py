# apps/reports/models.py

from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User
from apps.workspaces.models import Workspace

def validate_student_user(user_id):
    """Only accepts users of type 'STUDENT'."""
    user = User.objects.get(pk=user_id)
    if user.user_type != 'STUDENT':
        raise ValidationError("Only users of type 'STUDENT' are allowed.")

def validate_staff_user(user_id):
    """Only accepts users of type 'STAFF' or 'ADMIN'."""
    user = User.objects.get(pk=user_id)
    if user.user_type not in ['STAFF', 'ADMIN']:
        raise ValidationError("Only users of type 'STAFF' or 'ADMIN' are allowed.")

class DailyReport(models.Model):
    """Model for each student's daily report."""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_reports', validators=[validate_student_user])
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='daily_reports')
    report_date = models.DateField(verbose_name="Report date")
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Hours worked")
    work_description = models.TextField(verbose_name="Work description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_reports'
        ordering = ['-report_date']
        unique_together = ('student', 'report_date', 'workspace')
        verbose_name = "Daily Report"
        verbose_name_plural = "Daily Reports"

    def __str__(self):
        return f"{self.student.get_full_name()} report ({self.workspace.name}) - {self.report_date}"

class SalaryRecord(models.Model):
    """Model for each student's monthly salary record."""
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_records', validators=[validate_student_user])
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='salary_records')
    month = models.IntegerField(verbose_name="Month")
    year = models.IntegerField(verbose_name="Year")
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Total hours")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Hourly rate")
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Gross amount (total)")
    deduction_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'), verbose_name="Deduction percentage (%)")
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Deduction amount")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Net amount (take-home)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_salaries', validators=[validate_staff_user])
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'salary_records'
        ordering = ['-year', '-month']
        unique_together = ('student', 'workspace', 'year', 'month')
        verbose_name = "Monthly Salary Record"
        verbose_name_plural = "Monthly Salary Records"

    def save(self, *args, **kwargs):
        self.gross_amount = Decimal(self.total_hours) * Decimal(self.hourly_rate)
        self.deduction_amount = (self.gross_amount * Decimal(self.deduction_percentage)) / Decimal(100)
        self.net_amount = self.gross_amount - self.deduction_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.get_full_name()} for salary ({self.workspace.name}) - {self.year}/{self.month}"

class MonthlyReport(models.Model):
    """Model for each student's monthly Excel report."""
    STATUS_CHOICES = (
        ('GENERATED', 'Generated'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_reports', validators=[validate_student_user])
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='monthly_reports')
    salary = models.OneToOneField(SalaryRecord, on_delete=models.CASCADE, related_name='monthly_report')
    month = models.IntegerField()
    year = models.IntegerField()
    file = models.FileField(upload_to='monthly_reports/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATED')
    managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_reports', validators=[validate_staff_user])
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monthly_reports'
        ordering = ['-year', '-month']
        unique_together = ('student', 'workspace', 'year', 'month')
        verbose_name = "Monthly Report"
        verbose_name_plural = "Monthly Reports"

    def __str__(self):
        return f"{self.student.get_full_name()} for monthly report ({self.workspace.name}) - {self.year}/{self.month}"