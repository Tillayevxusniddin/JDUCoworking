# apps/reports/views.py

from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import DailyReport, MonthlyReport, SalaryRecord
from .serializers import (
    DailyReportSerializer, MonthlyReportSerializer, SalaryRecordSerializer,
    MonthlyReportManageSerializer, SalaryPaidSerializer
)
from .permissions import IsStudent, IsStaffOrAdmin, IsOwnerOrStaffAdmin

@extend_schema_view(
    list=extend_schema(summary="📄 Mening kunlik hisobotlarim", tags=['Hisobotlar (Kunlik)']),
    create=extend_schema(summary="✍️ Yangi kunlik hisobot yaratish", tags=['Hisobotlar (Kunlik)']),
)
class DailyReportViewSet(viewsets.ModelViewSet):
    serializer_class = DailyReportSerializer
    permission_classes = [IsStudent]
    def get_queryset(self):
        return DailyReport.objects.filter(student=self.request.user)

@extend_schema_view(
    list=extend_schema(summary="📑 [STAFF] Oylik hisobotlar ro'yxati", tags=['Hisobotlar (Oylik)']),
    retrieve=extend_schema(summary="📑 [STAFF/Owner] Bitta oylik hisobotni ko'rish", tags=['Hisobotlar (Oylik)']),
    manage_report=extend_schema(request=MonthlyReportManageSerializer, summary="📊 [STAFF] Oylik hisobotni boshqarish", tags=['Hisobotlar (Oylik)']),
)
class MonthlyReportViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MonthlyReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student__id', 'year', 'month', 'status']
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']:
            return MonthlyReport.objects.select_related('student', 'salary').all()
        return MonthlyReport.objects.filter(student=user).select_related('student', 'salary')
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
        return Response(self.get_serializer(report).data)

@extend_schema_view(
    list=extend_schema(summary="💰 Maosh yozuvlari ro'yxati", tags=['Maoshlar']),
    retrieve=extend_schema(summary="💰 Bitta maosh yozuvini ko'rish", tags=['Maoshlar']),
    mark_as_paid=extend_schema(request=SalaryPaidSerializer, summary="💵 [STAFF] Maoshni 'To'langan' deb belgilash", tags=['Maoshlar']),
)
class SalaryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SalaryRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']: return SalaryRecord.objects.all().select_related('student')
        return SalaryRecord.objects.filter(student=user).select_related('student')
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
        return Response(self.get_serializer(salary_record).data)