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
    list=extend_schema(summary="All Projects List", tags=['Projects']),
    retrieve=extend_schema(summary="Project Details", tags=['Projects']),
    create=extend_schema(summary="[ADMIN] Create New Project", request=JobCreateUpdateSerializer, tags=['Projects']),
    update=extend_schema(summary="[ADMIN] Edit Project", request=JobCreateUpdateSerializer, tags=['Projects']),
    partial_update=extend_schema(summary="[ADMIN] Partially Edit Project", request=JobCreateUpdateSerializer, tags=['Projects']),
    destroy=extend_schema(summary="[ADMIN] Delete Project", tags=['Projects']),
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
        """Specifies the job creator."""
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(summary="All Vacancies List", tags=['Vacancies']),
    retrieve=extend_schema(summary="Vacancy Details", tags=['Vacancies']),
    create=extend_schema(summary="[STAFF] Create New Vacancy", request=JobVacancyCreateUpdateSerializer, tags=['Vacancies']),
    update=extend_schema(summary="[STAFF] Edit Vacancy", request=JobVacancyCreateUpdateSerializer, tags=['Vacancies']),
    partial_update=extend_schema(summary="[STAFF] Partially Edit Vacancy", request=JobVacancyCreateUpdateSerializer, tags=['Vacancies']),
    destroy=extend_schema(summary="[STAFF] Delete Vacancy", tags=['Vacancies']),
)
class JobVacancyViewSet(viewsets.ModelViewSet):
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
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="All Applications List", 
        tags=['Applications'],
        parameters=[OpenApiParameter(name='vacancy_id', type=OpenApiTypes.INT, description='Filter by Vacancy ID')]
    ),
    retrieve=extend_schema(summary="Application Details", tags=['Applications']),
    create=extend_schema(summary="[STUDENT] Apply for Vacancy", request=VacancyApplicationCreateSerializer, tags=['Applications']),
    update=extend_schema(summary="[STAFF] Change Application Status", request=VacancyApplicationManageSerializer, tags=['Applications']),
    partial_update=extend_schema(summary="[STAFF] Change Application Status", request=VacancyApplicationManageSerializer, tags=['Applications']),
    destroy=extend_schema(summary="[Applicant] Withdraw Application", tags=['Applications']),
)
class VacancyApplicationViewSet(viewsets.ModelViewSet):
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
        application = serializer.save(applicant=self.request.user)
        vacancy_creator = application.vacancy.created_by
        
        create_notification(
            recipient=vacancy_creator,
            actor=application.applicant,
            verb="Your application has been submitted.",
            message=f"'{application.applicant.get_full_name()}' has submitted an application for the '{application.vacancy.title}' vacancy.",
            action_object=application
        )
    
    def perform_update(self, serializer):
        application = serializer.save()
        new_status = application.status
        if not hasattr(application, '_reviewed_by_user'):
             application._reviewed_by_user = self.request.user
        
        if new_status == 'REVIEWING':
            create_notification(
                recipient=application.applicant,
                actor=self.request.user,
                verb="Your application is under review.",
                message=f"Your application for the '{application.vacancy.title}' vacancy is being reviewed.",
                action_object=application
            )
        elif new_status == 'REJECTED':
             create_notification(
                recipient=application.applicant,
                actor=self.request.user,
                verb="Your application has been rejected.",
                message=f"Unfortunately, your application for the '{application.vacancy.title}' vacancy has been rejected.",
                action_object=application
            )