# apps/users/views.py

from rest_framework import viewsets, status, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, Student, Recruiter, Staff
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    StudentProfileSerializer, StudentProfilePersonalUpdateSerializer, StudentProfileAdminUpdateSerializer,
    RecruiterProfileSerializer, RecruiterProfileUpdateSerializer,
    StaffProfileSerializer, StaffProfileUpdateSerializer,
    LoginSerializer, ChangePasswordSerializer, LogoutSerializer
)
from .permissions import (
    IsAdminUser, IsStaffUser, IsRecruiterUser, IsStudentUser, IsAdminOrStaff
)

from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    login=extend_schema(
        summary="🔑 User login",
        description="Foydalanuvchi tizimga kirishi va JWT tokenlarni olishi.",
        tags=["Authentication"],
        request=LoginSerializer,
    ),
    logout=extend_schema(
        summary="🚪 User logout",
        description="Refresh tokenni bekor qilish va tizimdan chiqish.",
        tags=["Authentication"],
        request=LogoutSerializer,
    ),
    change_password=extend_schema(
        summary="🔐 Change password",
        description="Foydalanuvchi parolini o'zgartirish.",
        tags=["Authentication"],
        request=ChangePasswordSerializer,
    )
)
class AuthViewSet(viewsets.GenericViewSet):
    """
    🔐 Authentication endpoints: Login, Logout, Change Password.
    Bu endpointlar uchun umumiy ruxsat berilgan (AllowAny).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer  # Default serializer

    def get_serializer_class(self):
        """Amalga qarab tegishli serializer'ni tanlaydi."""
        if self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'logout':
            return LogoutSerializer
        return LoginSerializer

    @action(detail=False, methods=['post'])
    def login(self, request, *args, **kwargs):
        """Foydalanuvchi email va parol orqali tizimga kiradi."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request, *args, **kwargs):
        """Tizimdagi foydalanuvchi refresh token yordamida tizimdan chiqadi."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Muvaffaqiyatli chiqildi'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Noto\'g\'ri yoki muddati o\'tgan token'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request, *args, **kwargs):
        """Tizimdagi foydalanuvchi eski va yangi parolni kiritib, parolini o'zgartiradi."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Parol muvaffaqiyatli o\'zgartirildi'}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(summary="👥 List all users (Admin only)", tags=["User Management"]),
    retrieve=extend_schema(summary="👤 Retrieve user (Admin only)", tags=["User Management"]),
    create=extend_schema(summary="➕ Create user (Admin only)", request=UserCreateSerializer, tags=["User Management"]),
    update=extend_schema(summary="✏️ Update user (Admin only)", request=UserUpdateSerializer, tags=["User Management"]),
    partial_update=extend_schema(summary="📝 Partial update user (Admin only)", request=UserUpdateSerializer, tags=["User Management"]),
    destroy=extend_schema(summary="🗑️ Delete user (Admin only)", tags=["User Management"]),
    me=extend_schema(summary="👤 Get current user", tags=["User Management"])
)
class UserManagementViewSet(viewsets.ModelViewSet):
    """
    👥 User Management endpoints for Admins (Full CRUD on User model).
    Profil avtomatik tarzda `create` yoki `partial_update`da yaratiladi/o'zgaradi.
    """
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user_type', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        """Amalga qarab tegishli serializer'ni tanlaydi."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """Joriy foydalanuvchining asosiy (User model) ma'lumotlarini qaytaradi."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- Reusable Base ViewSet for Profiles (without 'create' action) ---
class BaseProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    """
    Profil modellari uchun asosiy ViewSet. Bu ViewSet `create` amalini o'z ichiga olmaydi,
    chunki profillar avtomatik yaratiladi.
    """
    pass


@extend_schema_view(
    list=extend_schema(summary="🎓 List all student profiles", tags=["Student Profiles"]),
    retrieve=extend_schema(summary="🎓 Retrieve a student profile", tags=["Student Profiles"]),
    update=extend_schema(
        summary="✏️ [Admin/Staff] Update student profile",
        tags=["Student Profiles"],
        request=StudentProfileAdminUpdateSerializer
    ),
    partial_update=extend_schema(
        summary="📝 [Admin/Staff] Partial update student profile",
        tags=["Student Profiles"],
        request=StudentProfileAdminUpdateSerializer
    ),
    destroy=extend_schema(summary="🗑️ [Admin/Staff] Delete student profile", tags=["Student Profiles"]),
    me=extend_schema(
        summary="getMyStudentProfile 🎓 Get/Update my student profile",
        tags=["Student Profiles"],
        request=StudentProfilePersonalUpdateSerializer
    )
)
class StudentProfileViewSet(BaseProfileViewSet):
    """Talaba profillarini boshqarish uchun endpointlar."""
    queryset = Student.objects.select_related('user').all()

    def get_serializer_class(self):
        user = self.request.user
        if self.action in ['list', 'retrieve']:
            return StudentProfileSerializer
        if self.action == 'me' and user.user_type == 'STUDENT':
             return StudentProfilePersonalUpdateSerializer
        if user.user_type in ['ADMIN', 'STAFF']:
            return StudentProfileAdminUpdateSerializer
        return StudentProfileSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'me':
            self.permission_classes = [permissions.IsAuthenticated, IsStudentUser]
        else: # update, partial_update, destroy
            self.permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset
        return self.queryset.none()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request, *args, **kwargs):
        """Talabaga o'z profilini olish va tahrirlash imkonini beradi."""
        try:
            instance = request.user.student_profile
        except Student.DoesNotExist:
            return Response({'error': 'Student profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'GET':
            serializer = StudentProfileSerializer(instance)
            return Response(serializer.data)
        
        serializer = self.get_serializer(instance, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StudentProfileSerializer(instance).data)


@extend_schema_view(
    list=extend_schema(summary="💼 List all recruiter profiles", tags=["Recruiter Profiles"]),
    retrieve=extend_schema(summary="💼 Retrieve a recruiter profile", tags=["Recruiter Profiles"]),
    update=extend_schema(
        summary="✏️ [Admin] Update recruiter profile",
        tags=["Recruiter Profiles"],
        request=RecruiterProfileUpdateSerializer
    ),
    partial_update=extend_schema(
        summary="📝 [Admin] Partial update recruiter profile",
        tags=["Recruiter Profiles"],
        request=RecruiterProfileUpdateSerializer
    ),
    destroy=extend_schema(summary="🗑️ [Admin] Delete recruiter profile", tags=["Recruiter Profiles"]),
    me=extend_schema(
        summary="getMyRecruiterProfile 💼 Get/Update my recruiter profile",
        tags=["Recruiter Profiles"],
        request=RecruiterProfileUpdateSerializer
    )
)
class RecruiterProfileViewSet(BaseProfileViewSet):
    """Recruiter profillarini boshqarish uchun endpointlar."""
    queryset = Recruiter.objects.select_related('user').all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecruiterProfileSerializer
        return RecruiterProfileUpdateSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'me':
            self.permission_classes = [permissions.IsAuthenticated, IsRecruiterUser]
        else: # update, partial_update, destroy
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset
        return self.queryset.none()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request, *args, **kwargs):
        """Recruiter'ga o'z profilini olish va tahrirlash imkonini beradi."""
        try:
            instance = request.user.recruiter_profile
        except Recruiter.DoesNotExist:
            return Response({'error': 'Recruiter profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'GET':
            return Response(RecruiterProfileSerializer(instance).data)
        
        serializer = self.get_serializer(instance, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecruiterProfileSerializer(instance).data)


@extend_schema_view(
    list=extend_schema(summary="👔 List all staff profiles", tags=["Staff Profiles"]),
    retrieve=extend_schema(summary="👔 Retrieve a staff profile", tags=["Staff Profiles"]),
    update=extend_schema(
        summary="✏️ [Admin] Update staff profile",
        tags=["Staff Profiles"],
        request=StaffProfileUpdateSerializer
    ),
    partial_update=extend_schema(
        summary="📝 [Admin] Partial update staff profile",
        tags=["Staff Profiles"],
        request=StaffProfileUpdateSerializer
    ),
    destroy=extend_schema(summary="🗑️ [Admin] Delete staff profile", tags=["Staff Profiles"]),
    me=extend_schema(
        summary="getMyStaffProfile 👔 Get/Update my staff profile",
        tags=["Staff Profiles"],
        request=StaffProfileUpdateSerializer
    )
)
class StaffProfileViewSet(BaseProfileViewSet):
    """Xodim (staff) profillarini boshqarish uchun endpointlar."""
    queryset = Staff.objects.select_related('user').all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return StaffProfileSerializer
        return StaffProfileUpdateSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'me':
            self.permission_classes = [permissions.IsAuthenticated, IsStaffUser]
        else: # update, partial_update, destroy
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset
        return self.queryset.none()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request, *args, **kwargs):
        """Xodimga (staff) o'z profilini olish va tahrirlash imkonini beradi."""
        try:
            instance = request.user.staff_profile
        except Staff.DoesNotExist:
            return Response({'error': 'Xodim profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'GET':
            return Response(StaffProfileSerializer(instance).data)
        
        serializer = self.get_serializer(instance, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StaffProfileSerializer(instance).data)