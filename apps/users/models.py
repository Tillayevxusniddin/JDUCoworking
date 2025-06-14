from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a 'User' with an email, password and other fields.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email, password and other fields.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser uchun is_staff=True bo‘lishi kerak.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser uchun is_superuser=True bo‘lishi kerak.')

            # Username ni email bilan bir xil qilib qo‘yamiz
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('STUDENT', 'Student'),
        ('STAFF', 'Staff'),
        ('RECRUITER', 'Recruiter'),
        ('ADMIN', 'Admin'),
    )
    
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='STUDENT')
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user_type})"

class Student(models.Model):

    YEAR_CHOICES = [(i, f"{i}-Year") for i in range(1, 6)]
    SEMESTER_CHOICES = [(1, '1st Semester'), (2, '2nd Semester')]
    LEVEL_STATUS_CHOICES = [('SIMPLE', 'Simple Student'), ('TEAMLEAD', 'Team Leader')]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,  # <-- Bo'sh qoldirishga ruxsat berish
        null=True,  # <-- Null qiymatga ruxsat berish
        default=None  # <-- Default qiymat
    )
    it_skills = models.JSONField(default=list, blank=True)
    semester = models.IntegerField(choices=SEMESTER_CHOICES, blank=True, null=True)
    year_of_study = models.IntegerField(choices=YEAR_CHOICES, blank=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    resume_file = models.FileField(
        upload_to='resumes/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    level_status = models.CharField(
        max_length=20,
        choices=LEVEL_STATUS_CHOICES,
        default='SIMPLE'
    )
    jlpt = models.CharField(max_length=10, blank=True, null=True)
    ielts = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['user__email']

class Recruiter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')
    company_name = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    company_website = models.URLField(blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.company_name}"
    
    class Meta:
        db_table = 'recruiters'
        ordering = ['user__email']

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    position = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staffs'
        ordering = ['user__email']
    
    def __str__(self):
        return f"{self.user.username} - {self.position}"
