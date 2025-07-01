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
    list=extend_schema(summary="📄 Mening kunlik hisobotlarim ro'yxati", tags=['Hisobotlar (Kunlik)']),
    retrieve=extend_schema(summary="📄 Bitta kunlik hisobotni ko'rish", tags=['Hisobotlar (Kunlik)']),
    create=extend_schema(summary="✍️ Yangi kunlik hisobot yaratish", tags=['Hisobotlar (Kunlik)']),
    update=extend_schema(summary="✏️ Kunlik hisobotni tahrirlash", tags=['Hisobotlar (Kunlik)']),
    partial_update=extend_schema(summary="📝 Kunlik hisobotni qisman tahrirlash", tags=['Hisobotlar (Kunlik)']),
    destroy=extend_schema(summary="🗑️ Kunlik hisobotni o'chirish", tags=['Hisobotlar (Kunlik)']),
)
class DailyReportViewSet(viewsets.ModelViewSet):
    """
    Talabalar o'zlarining kunlik hisobotlarini yaratishi va boshqarishi uchun.
    Har bir talaba faqat o'zining hisobotlari ustida amal bajara oladi.
    """
    serializer_class = DailyReportSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        """Foydalanuvchi faqat o'zining kunlik hisobotlarini ko'ra oladi."""
        return DailyReport.objects.filter(student=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="📑 [STAFF] Barcha oylik hisobotlar ro'yxati",
        tags=['Hisobotlar (Oylik)'],
        parameters=[
            OpenApiParameter(name='student__id', type=OpenApiTypes.INT, description='Talaba ID si bo\'yicha filtrlash'),
            OpenApiParameter(name='year', type=OpenApiTypes.INT, description='Yil bo\'yicha filtrlash'),
            OpenApiParameter(name='month', type=OpenApiTypes.INT, description='Oy bo\'yicha filtrlash'),
            OpenApiParameter(name='status', type=OpenApiTypes.STR, description='Status bo\'yicha filtrlash (GENERATED, APPROVED, REJECTED)'),
        ]
    ),
    retrieve=extend_schema(summary="📑 [STAFF/Owner] Bitta oylik hisobotni ko'rish", tags=['Hisobotlar (Oylik)']),
    manage_report=extend_schema(
        summary="📊 [STAFF] Oylik hisobotni tasdiqlash/rad etish",
        tags=['Hisobotlar (Oylik)'],
        request=MonthlyReportManageSerializer
    ),
)
class MonthlyReportViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    """
    Staff/Admin oylik hisobotlarni ko'rishi, filtrlashi va boshqarishi uchun.
    Student faqat o'zinikini ko'ra oladi (`retrieve`).
    """
    serializer_class = MonthlyReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student__id', 'year', 'month', 'status']

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']:
            return MonthlyReport.objects.select_related('student', 'salary').all()
        elif user.user_type == 'STUDENT':
            return MonthlyReport.objects.filter(student=user).select_related('student', 'salary')
        return MonthlyReport.objects.none()

    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = [IsOwnerOrStaffAdmin]
        else:
            self.permission_classes = [IsStaffOrAdmin]
        return super().get_permissions()

    @action(detail=True, methods=['patch'], url_path='manage')
    def manage_report(self, request, pk=None):
        """Oylik hisobotni tasdiqlash yoki rad etish."""
        report = self.get_object()
        serializer = MonthlyReportManageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data.get('status')
        rejection_reason = serializer.validated_data.get('rejection_reason')

        # Asosiy hisobot statusini yangilash
        report.status = new_status
        report.managed_by = request.user
        
        # Bog'liq bo'lgan maosh yozuvi statusini sinxronlashtirish
        salary_record = report.salary
        salary_record.status = new_status
        
        if new_status == 'APPROVED':
            salary_record.approved_by = request.user
            salary_record.approved_at = timezone.now()
            report.rejection_reason = None
        else:  # REJECTED
            report.rejection_reason = rejection_reason
            salary_record.approved_by = None
            salary_record.approved_at = None

        report.save()
        salary_record.save()
        
        return Response(self.get_serializer(report).data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(summary="💰 Maosh yozuvlari ro'yxati", tags=['Maoshlar']),
    retrieve=extend_schema(summary="💰 Bitta maosh yozuvini ko'rish", tags=['Maoshlar']),
    mark_as_paid=extend_schema(
        summary="💵 [STAFF] Maoshni 'To'langan' deb belgilash",
        tags=['Maoshlar'],
        request=SalaryPaidSerializer # Bo'sh so'rov
    ),
)
class SalaryViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    """
    Maosh yozuvlarini ko'rish va to'langanini belgilash uchun.
    Student faqat o'zinikini, Staff/Admin hammanikini ko'radi.
    """
    serializer_class = SalaryRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['STAFF', 'ADMIN']:
            return SalaryRecord.objects.all().select_related('student')
        elif user.user_type == 'STUDENT':
            return SalaryRecord.objects.filter(student=user).select_related('student')
        return SalaryRecord.objects.none()

    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = [IsOwnerOrStaffAdmin]
        # 'list' va 'mark_as_paid' uchun standart ruxsatnomalar ishlaydi
        return super().get_permissions()

    @action(detail=True, methods=['patch'], url_path='mark-as-paid')
    def mark_as_paid(self, request, pk=None):
        """Maoshni 'To'langan' deb belgilash."""
        salary_record = self.get_object()
        if salary_record.status != 'APPROVED':
            return Response(
                {'error': "Faqat 'Tasdiqlangan' (APPROVED) statusidagi maoshni to'langan deb belgilash mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )
        salary_record.status = 'PAID'
        salary_record.paid_at = timezone.now()
        salary_record.save()
        return Response(self.get_serializer(salary_record).data)