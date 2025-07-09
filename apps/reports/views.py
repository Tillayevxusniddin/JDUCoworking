# apps/reports/views.py

from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import DailyReport, MonthlyReport, SalaryRecord
# ✅ YANGILANGAN IMPORTLAR
from .serializers import (
    DailyReportListSerializer, DailyReportDetailSerializer, DailyReportCreateSerializer,
    MonthlyReportListSerializer, MonthlyReportDetailSerializer,
    SalaryRecordListSerializer, SalaryRecordDetailSerializer,
    MonthlyReportManageSerializer, SalaryPaidSerializer
)
from .permissions import IsStudent, IsStaffOrAdmin, IsOwnerOrStaffAdmin
from apps.notifications.utils import create_notification


@extend_schema_view(
    list=extend_schema(summary="📄 Mening kunlik hisobotlarim", tags=['Hisobotlar (Kunlik)']),
    create=extend_schema(summary="✍️ Yangi kunlik hisobot yaratish", tags=['Hisobotlar (Kunlik)']),
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
        """Talabani avtomatik `student` maydoniga saqlaydi."""
        serializer.save(student=self.request.user)

@extend_schema_view(
    list=extend_schema(summary="📑 [STAFF] Oylik hisobotlar ro'yxati", tags=['Hisobotlar (Oylik)']),
    retrieve=extend_schema(summary="📑 [STAFF/Owner] Bitta oylik hisobotni ko'rish", tags=['Hisobotlar (Oylik)']),
    manage_report=extend_schema(request=MonthlyReportManageSerializer, summary="📊 [STAFF] Oylik hisobotni boshqarish", tags=['Hisobotlar (Oylik)']),
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

        status_text = "tasdiqlandi" if new_status == 'APPROVED' else "rad etildi"
        message = f"Sizning {report.year}-{report.month} oyi uchun '{report.workspace.name}' ish maydonidagi hisobotingiz {status_text}."
        if new_status == 'REJECTED':
            message += f" Sabab: {report.rejection_reason}"
            
        create_notification(
            recipient=report.student,
            actor=request.user,
            verb=f"hisobotingizni {status_text}",
            message=message,
            action_object=report
        )
        return Response(self.get_serializer(report).data)

@extend_schema_view(
    list=extend_schema(summary="💰 Maosh yozuvlari ro'yxati", tags=['Maoshlar']),
    retrieve=extend_schema(summary="💰 Bitta maosh yozuvini ko'rish", tags=['Maoshlar']),
    mark_as_paid=extend_schema(request=SalaryPaidSerializer, summary="💵 [STAFF] Maoshni 'To'langan' deb belgilash", tags=['Maoshlar']),
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
            return Response({'error': "Faqat 'Tasdiqlangan' maoshni to'langan deb belgilash mumkin."}, status=status.HTTP_400_BAD_REQUEST)
        salary_record.status = 'PAID'; salary_record.paid_at = timezone.now(); salary_record.save()
    
        create_notification(
            recipient=salary_record.student,
            actor=request.user,
            verb="maoshingizni to'ladi",
            message=f"Sizning {salary_record.year}-{salary_record.month} oyi uchun '{salary_record.workspace.name}'dagi maoshingiz to'landi.",
            action_object=salary_record
        )
        return Response(self.get_serializer(salary_record).data)