# apps/reports/views.py

from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import DailyReport, MonthlyReport, SalaryRecord
from .serializers import (
    DailyReportListSerializer, DailyReportDetailSerializer, DailyReportCreateSerializer,
    MonthlyReportListSerializer, MonthlyReportDetailSerializer,
    SalaryRecordListSerializer, SalaryRecordDetailSerializer,
    MonthlyReportManageSerializer, SalaryPaidSerializer
)
from .permissions import IsStudent, IsStaffOrAdmin, IsOwnerOrStaffAdmin
from apps.notifications.utils import create_notification


@extend_schema_view(
    list=extend_schema(summary="📄 My Daily Reports", tags=['Reports (Daily)']),
    create=extend_schema(summary="✍️ Create New Daily Report", tags=['Reports (Daily)']),
)
class DailyReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStudent]
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return DailyReport.objects.none()
        return DailyReport.objects.filter(student=self.request.user)
    def get_serializer_class(self):
        if self.action == 'list':
            return DailyReportListSerializer
        if self.action == 'create':
            return DailyReportCreateSerializer
        return DailyReportDetailSerializer # retrieve, update, etc.
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

@extend_schema_view(
    list=extend_schema(summary="📑 [STAFF] List of Monthly Reports", tags=['Reports (Monthly)']),
    retrieve=extend_schema(summary="📑 [STAFF/Owner] View a Monthly Report", tags=['Reports (Monthly)']),
    manage_report=extend_schema(request=MonthlyReportManageSerializer, summary="📊 [STAFF] Manage a Monthly Report", tags=['Reports (Monthly)']),
)
class MonthlyReportViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student__id', 'year', 'month', 'status']
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MonthlyReport.objects.none()
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']:
            return MonthlyReport.objects.select_related('student', 'salary').all()
        return MonthlyReport.objects.filter(student=user).select_related('student', 'salary')
    def get_serializer_class(self):
        if self.action == 'list':
            return MonthlyReportListSerializer
        if self.action == 'manage_report':
            return MonthlyReportManageSerializer
        return MonthlyReportDetailSerializer # retrieve
    def get_permissions(self):
        if self.action == 'retrieve': self.permission_classes = [IsOwnerOrStaffAdmin]
        elif self.action == 'manage_report': self.permission_classes = [IsStaffOrAdmin]
        return super().get_permissions()
    
    @action(detail=True, methods=['patch'], url_path='manage')
    def manage_report(self, request, pk=None):
        report = self.get_object(); serializer = MonthlyReportManageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get('status')
        report.status=new_status; report.managed_by=request.user; report.salary.status=new_status
        if new_status == 'APPROVED':
            report.salary.approved_by=request.user; report.salary.approved_at=timezone.now(); report.rejection_reason=None
        else:
            report.rejection_reason=serializer.validated_data.get('rejection_reason'); report.salary.approved_by=None; report.salary.approved_at=None
        report.save(); report.salary.save()

        status_text = "approved" if new_status == 'APPROVED' else "rejected"
        message = f"Your report for {report.year}-{report.month} in the '{report.workspace.name}' workspace has been {status_text}."
        if new_status == 'REJECTED':
            message += f" Reason: {report.rejection_reason}"

        create_notification(
            recipient=report.student,
            actor=request.user,
            verb=f"Your report has been {status_text}",
            message=message,
            action_object=report
        )
        return Response(self.get_serializer(report).data)

@extend_schema_view(
    list=extend_schema(summary="💰 List of Salary Records", tags=['Salaries']),
    retrieve=extend_schema(summary="💰 View a Salary Record", tags=['Salaries']),
    mark_as_paid=extend_schema(request=SalaryPaidSerializer, summary="💵 [STAFF] Mark Salary as 'Paid'", tags=['Salaries']),
)
class SalaryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SalaryRecord.objects.none()
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']: return SalaryRecord.objects.all().select_related('student')
        return SalaryRecord.objects.filter(student=user).select_related('student')
    def get_serializer_class(self):
        if self.action == 'list':
            return SalaryRecordListSerializer
        if self.action == 'mark_as_paid':
            return SalaryPaidSerializer
        return SalaryRecordDetailSerializer # retrieve
    def get_permissions(self):
        if self.action == 'retrieve': self.permission_classes = [IsOwnerOrStaffAdmin]
        elif self.action == 'mark_as_paid': self.permission_classes = [IsStaffOrAdmin]
        return super().get_permissions()

    @action(detail=True, methods=['patch'], url_path='mark-as-paid')
    def mark_as_paid(self, request, pk=None):
        salary_record = self.get_object()
        if salary_record.status != 'APPROVED':
            return Response({'error': "Only approved salaries can be marked as paid."}, status=status.HTTP_400_BAD_REQUEST)
        salary_record.status = 'PAID'; salary_record.paid_at = timezone.now(); salary_record.save()
    
        create_notification(
            recipient=salary_record.student,
            actor=request.user,
            verb="Salary Paid",
            message=f"Your salary for {salary_record.year}-{salary_record.month} in the '{salary_record.workspace.name}' workspace has been paid.",
            action_object=salary_record
        )
        return Response(self.get_serializer(salary_record).data)