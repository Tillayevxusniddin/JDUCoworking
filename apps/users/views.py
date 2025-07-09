# apps/users/views.py

from rest_framework import viewsets, status, permissions, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User, Student, Recruiter, Staff
from .serializers import (
    UserDetailSerializer, UserSummarySerializer, UserCreateSerializer, UserUpdateSerializer,
    StudentProfileListSerializer, StudentProfileDetailSerializer, 
    StudentProfilePersonalUpdateSerializer, StudentProfileAdminUpdateSerializer,
    RecruiterProfileListSerializer, RecruiterProfileDetailSerializer, RecruiterProfileUpdateSerializer,
    StaffProfileListSerializer, StaffProfileDetailSerializer, StaffProfileUpdateSerializer,
    ChangePasswordSerializer
)
from .permissions import IsAdminUser, IsStaffUser, IsRecruiterUser, IsStudentUser, IsAdminOrStaff, IsProfileOwner

@extend_schema(summary="🔐 Parolni o'zgartirish", tags=["Authentication"])
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"message": "Parol muvaffaqiyatli o'zgartirildi."}, status=status.HTTP_200_OK)

@extend_schema_view(
    list=extend_schema(summary="👥 [ADMIN] Barcha foydalanuvchilar ro'yxati", tags=["User Management"]),
    retrieve=extend_schema(summary="👤 [ADMIN] Bitta foydalanuvchini olish", tags=["User Management"]),
    create=extend_schema(summary="➕ [ADMIN] Foydalanuvchi yaratish", tags=["User Management"]),
    update=extend_schema(summary="✏️ [ADMIN] Foydalanuvchini tahrirlash", tags=["User Management"]),
    partial_update=extend_schema(summary="📝 [ADMIN] Foydalanuvchini qisman tahrirlash", tags=["User Management"]),
    destroy=extend_schema(summary="🗑️ [ADMIN] Foydalanuvchini o'chirish", tags=["User Management"]),
    me=extend_schema(summary="👤 Joriy foydalanuvchi ma'lumotlari", tags=["User Management"])
)
class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user_type', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        if self.action == 'list': return UserSummarySerializer
        if self.action == 'create': return UserCreateSerializer
        if self.action in ['update', 'partial_update']: return UserUpdateSerializer
        return UserDetailSerializer

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request, *args, **kwargs):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BaseProfileViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin, mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    pass

@extend_schema_view(
    list=extend_schema(summary="🎓 Barcha talaba profillari", tags=["Student Profiles"]),
    retrieve=extend_schema(summary="🎓 Bitta talaba profili", tags=["Student Profiles"]),
    update=extend_schema(summary="✏️ [ADMIN/STAFF] Talaba profilini tahrirlash", tags=["Student Profiles"]),
    me=extend_schema(summary="🎓 Mening profilim (Talaba)", tags=["Student Profiles"])
)
class StudentProfileViewSet(BaseProfileViewSet):
    queryset = Student.objects.select_related('user').all()
    
    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False): return StudentProfileListSerializer
        user = self.request.user
        if self.action == 'list': return StudentProfileListSerializer
        if self.action == 'me': return StudentProfilePersonalUpdateSerializer
        if user.user_type in ['ADMIN', 'STAFF']: return StudentProfileAdminUpdateSerializer
        return StudentProfileDetailSerializer

    def get_permissions(self):
        if self.action == 'me': self.permission_classes = [IsStudentUser]
        elif self.action in ['update', 'partial_update', 'destroy']: self.permission_classes = [IsAdminOrStaff]
        else: self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request, *args, **kwargs):
        instance = self.request.user.student_profile
        if request.method == 'GET':
            # ✅ TUZATILGAN QISM: To'liq ma'lumot qaytaramiz
            serializer = StudentProfileDetailSerializer(instance)
            return Response(serializer.data)
        serializer = self.get_serializer(instance, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StudentProfileDetailSerializer(instance).data)

@extend_schema_view(
    list=extend_schema(summary="💼 Barcha recruiter profillari", tags=["Recruiter Profiles"]),
    retrieve=extend_schema(summary="💼 Bitta recruiter profili", tags=["Recruiter Profiles"]),
    me=extend_schema(summary="💼 Mening profilim (Recruiter)", tags=["Recruiter Profiles"])
)
class RecruiterProfileViewSet(BaseProfileViewSet):
    queryset = Recruiter.objects.select_related('user').all()

    def get_serializer_class(self):
        if self.action == 'list': return RecruiterProfileListSerializer
        if self.action == 'me': return RecruiterProfileUpdateSerializer
        return RecruiterProfileDetailSerializer

    def get_permissions(self):
        if self.action == 'me': self.permission_classes = [IsRecruiterUser]
        elif self.action in ['update', 'partial_update', 'destroy']: self.permission_classes = [IsAdminUser]
        else: self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request, *args, **kwargs):
        instance = request.user.recruiter_profile
        if request.method == 'GET':
            # ✅ TUZATILGAN QISM: To'liq ma'lumot qaytaramiz
            serializer = RecruiterProfileDetailSerializer(instance)
            return Response(serializer.data)
        serializer = self.get_serializer(instance, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecruiterProfileDetailSerializer(instance).data)


@extend_schema_view(
    list=extend_schema(summary="👔 Barcha xodim profillari", tags=["Staff Profiles"]),
    retrieve=extend_schema(summary="👔 Bitta xodim profili", tags=["Staff Profiles"]),
    me=extend_schema(summary="👔 Mening profilim (Staff)", tags=["Staff Profiles"])
)
class StaffProfileViewSet(BaseProfileViewSet):
    queryset = Staff.objects.select_related('user').all()

    def get_serializer_class(self):
        if self.action == 'list': return StaffProfileListSerializer
        if self.action == 'me': return StaffProfileUpdateSerializer
        return StaffProfileDetailSerializer

    def get_permissions(self):
        if self.action == 'me': self.permission_classes = [IsStaffUser]
        elif self.action in ['update', 'partial_update', 'destroy']: self.permission_classes = [IsAdminUser]
        else: self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request, *args, **kwargs):
        instance = request.user.staff_profile
        if request.method == 'GET':
            # ✅ TUZATILGAN QISM: To'liq ma'lumot qaytaramiz
            serializer = StaffProfileDetailSerializer(instance)
            return Response(serializer.data)
        serializer = self.get_serializer(instance, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StaffProfileDetailSerializer(instance).data)
