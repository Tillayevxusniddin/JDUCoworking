# apps/jobs/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Job, JobVacancy, VacancyApplication
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateUpdateSerializer,
    JobVacancyListSerializer, JobVacancyDetailSerializer, JobVacancyCreateUpdateSerializer,
    VacancyApplicationListSerializer, VacancyApplicationDetailSerializer,
    VacancyApplicationCreateSerializer, VacancyApplicationManageSerializer
)
from .permissions import IsApplicantOrStaff, IsAdminOrReadOnly
from apps.users.permissions import IsAdminUser, IsAdminOrStaff, IsStudentUser
from apps.notifications.utils import create_notification


@extend_schema_view(
    list=extend_schema(summary="Barcha loyihalar ro'yxati", tags=['Loyihalar (Jobs)']),
    retrieve=extend_schema(summary="Bitta loyiha ma'lumotlari", tags=['Loyihalar (Jobs)']),
    create=extend_schema(summary="[ADMIN] Yangi loyiha yaratish", request=JobCreateUpdateSerializer, tags=['Loyihalar (Jobs)']),
    update=extend_schema(summary="[ADMIN] Loyihani tahrirlash", request=JobCreateUpdateSerializer, tags=['Loyihalar (Jobs)']),
    partial_update=extend_schema(summary="[ADMIN] Loyihani qisman tahrirlash", request=JobCreateUpdateSerializer, tags=['Loyihalar (Jobs)']),
    destroy=extend_schema(summary="[ADMIN] Loyihani o'chirish", tags=['Loyihalar (Jobs)']),
)
class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all().select_related('workspace', 'created_by')
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Job.objects.none()
        user = self.request.user
        if user.user_type == 'ADMIN':
            return self.queryset
        return self.queryset.filter(status='ACTIVE')
    def get_serializer_class(self):
        if self.action == 'list':
            return JobListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return JobCreateUpdateSerializer
        return JobDetailSerializer
    def perform_create(self, serializer):
        """Job yaratuvchisini avtomatik belgilaydi."""
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(summary="Barcha vakansiyalar ro'yxati", tags=['Vakansiyalar']),
    retrieve=extend_schema(summary="Bitta vakansiya ma'lumotlari", tags=['Vakansiyalar']),
    create=extend_schema(summary="[STAFF] Yangi vakansiya yaratish", request=JobVacancyCreateUpdateSerializer, tags=['Vakansiyalar']),
    update=extend_schema(summary="[STAFF] Vakansiyani tahrirlash", request=JobVacancyCreateUpdateSerializer, tags=['Vakansiyalar']),
    partial_update=extend_schema(summary="[STAFF] Vakansiyani qisman tahrirlash", request=JobVacancyCreateUpdateSerializer, tags=['Vakansiyalar']),
    destroy=extend_schema(summary="[STAFF] Vakansiyani o'chirish", tags=['Vakansiyalar']),
)
class JobVacancyViewSet(viewsets.ModelViewSet):
    """
    Vakansiyalar (JobVacancy) ustida amallar. STAFF to'liq huquqga ega.
    Talabalar faqat ochiq vakansiyalarni ko'ra oladi.
    """
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return JobVacancy.objects.none()
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']:
            return JobVacancy.objects.all().select_related('job', 'created_by')
        return JobVacancy.objects.filter(status='OPEN').select_related('job', 'created_by')

    def get_serializer_class(self):
        if self.action == 'list':
            return JobVacancyListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return JobVacancyCreateUpdateSerializer
        return JobVacancyDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrStaff()]
    
    def perform_create(self, serializer):
        """Vakansiya yaratuvchisini avtomatik belgilaydi."""
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Arizalar ro'yxati", 
        tags=['Arizalar'],
        parameters=[OpenApiParameter(name='vacancy_id', type=OpenApiTypes.INT, description='Vakansiya IDsi bo\'yicha filtrlash')]
    ),
    retrieve=extend_schema(summary="Bitta ariza ma'lumotlari", tags=['Arizalar']),
    create=extend_schema(summary="[STUDENT] Vakansiyaga ariza topshirish", request=VacancyApplicationCreateSerializer, tags=['Arizalar']),
    update=extend_schema(summary="[STAFF] Ariza statusini o'zgartirish", request=VacancyApplicationManageSerializer, tags=['Arizalar']),
    partial_update=extend_schema(summary="[STAFF] Ariza statusini o'zgartirish", request=VacancyApplicationManageSerializer, tags=['Arizalar']),
    destroy=extend_schema(summary="[Applicant] Arizani qaytarib olish", tags=['Arizalar']),
)
class VacancyApplicationViewSet(viewsets.ModelViewSet):
    """
    Vakansiyalarga topshirilgan arizalar (VacancyApplication) ustida amallar.
    """
    queryset = VacancyApplication.objects.all().select_related('applicant', 'vacancy__job')

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VacancyApplication.objects.none()
        
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']:
            vacancy_id = self.request.query_params.get('vacancy_id')
            
            queryset = self.queryset
            
            if vacancy_id:
                return queryset.filter(vacancy_id=vacancy_id)
            return queryset
        
        # ✅ TUZATILGAN QISM: qavslar olib tashlandi
        return self.queryset.filter(applicant=user)

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return VacancyApplicationListSerializer
        
        user = self.request.user
        if self.action == 'list':
            return VacancyApplicationListSerializer
        if self.action == 'create':
            return VacancyApplicationCreateSerializer
        if self.action in ['update', 'partial_update'] and user.user_type in ['STAFF', 'ADMIN']:
            return VacancyApplicationManageSerializer
        return VacancyApplicationDetailSerializer

    def get_permissions(self):
        if self.action == 'create': self.permission_classes = [IsStudentUser]
        elif self.action in ['update', 'partial_update']: self.permission_classes = [IsAdminOrStaff]
        elif self.action in ['destroy', 'retrieve']: self.permission_classes = [IsApplicantOrStaff]
        else: self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Talaba yangi ariza topshirganda vakansiya yaratuvchisiga bildirishnoma yuborish."""
        application = serializer.save(applicant=self.request.user)
        vacancy_creator = application.vacancy.created_by
        
        create_notification(
            recipient=vacancy_creator,
            actor=application.applicant,
            verb="sizning vakansiyangizga ariza topshirdi",
            message=f"'{application.applicant.get_full_name()}' siz yaratgan '{application.vacancy.title}' vakansiyasiga ariza topshirdi.",
            action_object=application
        )
    
    def perform_update(self, serializer):
        """
        Ariza statusi o'zgarganda (lekin 'ACCEPTED' emas) talabaga bildirishnoma yuborish.
        'ACCEPTED' holati signal orqali boshqariladi.
        """
        application = serializer.save()
        new_status = application.status
        
        # reviewed_by maydonini qo'lda to'ldiramiz, bu signal uchun kerak.
        if not hasattr(application, '_reviewed_by_user'):
             application._reviewed_by_user = self.request.user
        
        if new_status == 'REVIEWING':
            create_notification(
                recipient=application.applicant,
                actor=self.request.user,
                verb="arizangizni ko'rib chiqishni boshladi",
                message=f"Sizning '{application.vacancy.title}' vakansiyasiga topshirgan arizangiz ko'rib chiqilmoqda.",
                action_object=application
            )
        elif new_status == 'REJECTED':
             create_notification(
                recipient=application.applicant,
                actor=self.request.user,
                verb="arizangizni rad etdi",
                message=f"Afsuski, sizning '{application.vacancy.title}' vakansiyasiga topshirgan arizangiz rad etildi.",
                action_object=application
            )