from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import User, Student, Recruiter, Staff
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    StudentProfileSerializer, StudentUpdateSerializer,
    RecruiterProfileSerializer, RecruiterUpdateSerializer,
    StaffProfileSerializer, StaffUpdateSerializer,
    LoginSerializer, ChangePasswordSerializer
)
from .permissions import (
    IsAdminUser, IsStaffUser, IsRecruiterUser, IsStudentUser, IsProfileOwner
)


class AuthViewSet(viewsets.GenericViewSet):
    """Authentication endpoints for all users"""
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def get_serializer_class(self):
        if self.action == 'change_password':
            return ChangePasswordSerializer
        return LoginSerializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({'error': 'Refresh token majburiy'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Muvaffaqiyatli chiqildi'})
        except Exception:
            return Response({'error': 'Noto\'g\'ri token'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Parol muvaffaqiyatli o\'zgartirildi'})

class UserManagementViewSet(viewsets.ModelViewSet):
    """User management (Admin only)"""
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user_type', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class StudentProfileViewSet(viewsets.ModelViewSet):
    """Student profile management"""
    queryset = Student.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['level_status', 'semester', 'year_of_study']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'student_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        return StudentProfileSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        user = self.request.user
        if user.user_type == 'ADMIN':
            return self.queryset
        elif user.user_type == 'STAFF':
            return self.queryset
        elif user.user_type == 'STUDENT':
            return self.queryset.filter(user=user)
        return self.queryset.none()

    def has_object_permission(self, request, obj):
        if request.user.user_type == 'ADMIN':
            return True
        elif request.user.user_type == 'STAFF' and request.method in ['GET', 'PUT', 'PATCH']:
            return True
        return obj.user == request.user

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        try:
            instance = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({'error': 'Student profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = StudentProfileSerializer(instance)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = StudentUpdateSerializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(StudentProfileSerializer(instance).data)

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Profilni to‘g‘ridan-to‘g‘ri yaratish mumkin emas. User yaratish orqali avtomatik yaratiladi."},
            status=status.HTTP_403_FORBIDDEN
        )

class RecruiterProfileViewSet(viewsets.ModelViewSet):
    """Recruiter profile management"""
    queryset = Recruiter.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['company_name']
    search_fields = ['user__first_name', 'user__last_name', 'company_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return RecruiterUpdateSerializer
        return RecruiterProfileSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        user = self.request.user
        if user.user_type == 'ADMIN':
            return self.queryset
        elif user.user_type == 'RECRUITER':
            return self.queryset.filter(user=user)
        return self.queryset.none()

    def has_object_permission(self, request, obj):
        return request.user.user_type == 'ADMIN' or obj.user == request.user

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        try:
            instance = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response({'error': 'Recruiter profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = RecruiterProfileSerializer(instance)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = RecruiterUpdateSerializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(RecruiterProfileSerializer(instance).data)

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Profilni to‘g‘ridan-to‘g‘ri yaratish mumkin emas. User yaratish orqali avtomatik yaratiladi."},
            status=status.HTTP_403_FORBIDDEN
        )

class StaffProfileViewSet(viewsets.ModelViewSet):
    """Staff profile management"""
    queryset = Staff.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'position']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return StaffUpdateSerializer
        return StaffProfileSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        user = self.request.user
        if user.user_type == 'ADMIN':
            return self.queryset
        elif user.user_type == 'STAFF':
            return self.queryset.filter(user=user)
        return self.queryset.none()

    def has_object_permission(self, request, obj):
        return request.user.user_type == 'ADMIN' or obj.user == request.user

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        try:
            instance = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return Response({'error': 'Staff profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = StaffProfileSerializer(instance)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = StaffUpdateSerializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(StaffProfileSerializer(instance).data)

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Profilni to‘g‘ridan-to‘g‘ri yaratish mumkin emas. User yaratish orqali avtomatik yaratiladi."},
            status=status.HTTP_403_FORBIDDEN
        )