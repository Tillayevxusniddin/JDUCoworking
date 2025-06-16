from rest_framework import viewsets, status, permissions, mixins # <--- "mixins" shu yerga qo'shildi
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

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, extend_schema_view
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    login=extend_schema(
        summary="🔑 User login",
        description="Foydalanuvchi tizimga kirishi va JWT tokenlarni olishi",
        tags=["Authentication"],
        request=LoginSerializer,
        responses={
            200: {
                "description": "Muvaffaqiyatli login",
                "example": {
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "user_type": "STUDENT"
                    },
                    "access": "eyJhbGciOi...",
                    "refresh": "eyJhbGciOi..."
                }
            },
            400: {
                "description": "Noto'g'ri ma'lumotlar",
                "example": {"non_field_errors": ["Email yoki parol noto'g'ri"]}
            }
        },
        examples=[
            OpenApiExample(
                'Student login',
                description="Talaba tizimga kirishi",
                value={'email': 'student@example.com', 'password': 'password123'},
                request_only=True
            ),
            OpenApiExample(
                'Staff login',
                description="Xodim tizimga kirishi",
                value={'email': 'staff@example.com', 'password': 'password123'},
                request_only=True
            )
        ]
    ),
    logout=extend_schema(
        summary="🚪 User logout",
        description="Refresh tokenni bekor qilish va tizimdan chiqish",
        tags=["Authentication"],
        request={
            "type": "object",
            "properties": {
                "refresh": {
                    "type": "string",
                    "description": "Refresh token"
                }
            },
            "required": ["refresh"]
        },
        responses={
            200: {
                "description": "Muvaffaqiyatli logout",
                "example": {"message": "Muvaffaqiyatli chiqildi"}
            },
            400: {
                "description": "Noto'g'ri token",
                "example": {"error": "Noto'g'ri token"}
            }
        }
    ),
    change_password=extend_schema(
        summary="🔐 Change password",
        description="Foydalanuvchi parolini o'zgartirish",
        tags=["Authentication"],
        request=ChangePasswordSerializer,
        responses={
            200: {
                "description": "Parol muvaffaqiyatli o'zgartirildi",
                "example": {"message": "Parol muvaffaqiyatli o'zgartirildi"}
            },
            400: {
                "description": "Noto'g'ri ma'lumotlar",
                "example": {"old_password": ["Eski parol noto'g'ri"]}
            }
        }
    )
)
class AuthViewSet(viewsets.GenericViewSet):
    """
    🔐 Authentication endpoints
    
    Tizimga kirish, chiqish va parol o'zgartirish uchun endpointlar
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def get_serializer_class(self):
        if self.action == 'change_password':
            return ChangePasswordSerializer
        return LoginSerializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Foydalanuvchi tizimga kirishi"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Tizimdan chiqish va tokenni bekor qilish"""
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token majburiy'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Muvaffaqiyatli chiqildi'})
        except Exception:
            return Response(
                {'error': 'Noto\'g\'ri token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Parolni o'zgartirish"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Parol muvaffaqiyatli o\'zgartirildi'})


@extend_schema_view(
    list=extend_schema(
        summary="👥 List all users",
        description="Barcha foydalanuvchilar ro'yxati (faqat Admin)",
        tags=["User Management"],
        parameters=[
            OpenApiParameter(
                name='user_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Foydalanuvchi turi bo\'yicha filtrlash',
                enum=['STUDENT', 'STAFF', 'RECRUITER', 'ADMIN']
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Faol foydalanuvchilar bo\'yicha filtrlash'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Ism, familiya yoki email bo\'yicha qidirish'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Saralash (-created_at, created_at)',
                enum=['created_at', '-created_at']
            )
        ]
    ),
    retrieve=extend_schema(
        summary="👤 Retrieve user",
        description="Foydalanuvchi ma'lumotlarini olish (faqat Admin)",
        tags=["User Management"]
    ),
    create=extend_schema(
        summary="➕ Create user",
        description="Yangi foydalanuvchi yaratish (faqat Admin). Profili avtomatik yaratiladi.",
        tags=["User Management"],
        request=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: {
                "description": "Noto'g'ri ma'lumotlar",
                "example": {
                    "email": ["Bu email allaqachon mavjud"],
                    "password": ["Parollar mos kelmaydi"]
                }
            }
        }
    ),
    update=extend_schema(
        summary="✏️ Update user",
        description="Foydalanuvchi ma'lumotlarini to'liq yangilash (faqat Admin)",
        tags=["User Management"],
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    ),
    partial_update=extend_schema(
        summary="📝 Partial update user",
        description="Foydalanuvchi ma'lumotlarini qisman yangilash (faqat Admin)",
        tags=["User Management"],
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    ),
    destroy=extend_schema(
        summary="🗑️ Delete user",
        description="Foydalanuvchini o'chirish (faqat Admin)",
        tags=["User Management"]
    ),
    me=extend_schema(
        summary="👤 Get current user",
        description="Hozirgi tizimdagi foydalanuvchi ma'lumotlari",
        tags=["User Management"],
        responses={200: UserSerializer}
    )
)
class UserManagementViewSet(viewsets.ModelViewSet):
    """
    👥 User Management ViewSet
    
    Foydalanuvchilarni boshqarish uchun endpointlar (faqat Admin)
    """
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
        """Hozirgi foydalanuvchi ma'lumotlari"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ------------------- PROFIL VIEWSETLAR UCHUN O'ZGARISH JOYLARI -------------------

@extend_schema_view(
    # ... `create` uchun schema olib tashlandi
    list=extend_schema(
        summary="🎓 List all student profiles",
        description="Barcha talabalar profillari ro'yxati (Admin va Staff uchun)",
        tags=["Student Profiles"],
        parameters=[
            # ... filtrlash parametrlari o'zgarishsiz qoladi
        ]
    ),
    retrieve=extend_schema(summary="🎓 Retrieve student profile", tags=["Student Profiles"]),
    update=extend_schema(summary="✏️ Update student profile", tags=["Student Profiles"]),
    partial_update=extend_schema(summary="📝 Partial update student profile", tags=["Student Profiles"]),
    destroy=extend_schema(summary="🗑️ Delete student profile", tags=["Student Profiles"]),
)
class StudentProfileViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet): # <--- 1-O'ZGARISH: ModelViewSet o'rniga mixin'lar
    """
    🎓 Student Profile Management
    
    Talabalar profillari bilan ishlash (yangi profil yaratishdan tashqari)
    """
    queryset = Student.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['level_status', 'semester', 'year_of_study']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'student_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'me']:
            return StudentUpdateSerializer
        return StudentProfileSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        # ADMIN va STAFF barcha ro'yxatni ko'ra oladi
        elif self.action == 'list':
            return [permissions.IsAuthenticated(), IsAdminUser | IsStaffUser]
        # Qolgan barcha holatlarda tizimga kirgan bo'lishi kifoya (obyekt darajasida IsProfileOwner tekshiradi)
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # ... mantiq o'zgarishsiz qoladi
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        
        user = self.request.user
        if user.user_type in ['ADMIN', 'STAFF']:
            return self.queryset
        elif user.user_type == 'STUDENT':
            return self.queryset.filter(user=user)
        return self.queryset.none()

    def perform_update(self, serializer):
        # ... mantiq o'zgarishsiz qoladi
        instance = self.get_object()
        if not IsProfileOwner().has_object_permission(self.request, self, instance):
            self.permission_denied(self.request)
        serializer.save()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        # ... mantiq o'zgarishsiz qoladi
        try:
            instance = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({'error': 'Student profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = StudentProfileSerializer(instance)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = StudentUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StudentProfileSerializer(instance).data)

    # 2-O'ZGARISH: `create` metodi olib tashlandi, chunki u endi mavjud emas


@extend_schema_view(
    # ... `create` uchun schema olib tashlandi
    list=extend_schema(summary="💼 List all recruiter profiles", tags=["Recruiter Profiles"]),
    retrieve=extend_schema(summary="💼 Retrieve recruiter profile", tags=["Recruiter Profiles"]),
    update=extend_schema(summary="✏️ Update recruiter profile", tags=["Recruiter Profiles"]),
    partial_update=extend_schema(summary="📝 Partial update recruiter profile", tags=["Recruiter Profiles"]),
    destroy=extend_schema(summary="🗑️ Delete recruiter profile", tags=["Recruiter Profiles"]),
)
class RecruiterProfileViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.UpdateModelMixin,
                                mixins.DestroyModelMixin,
                                viewsets.GenericViewSet):
    """
    💼 Recruiter Profile Management
    """
    queryset = Recruiter.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['company_name']
    search_fields = ['user__first_name', 'user__last_name', 'company_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'me']:
            return RecruiterUpdateSerializer
        return RecruiterProfileSerializer
    
    # ... `get_permissions` va `get_queryset` mantiqlari StudentProfileViewSet'ga o'xshash
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return self.queryset.none()
        if user.user_type == 'ADMIN':
            return self.queryset
        elif user.user_type == 'RECRUITER':
            return self.queryset.filter(user=user)
        return self.queryset.none()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        try:
            instance = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response({'error': 'Recruiter profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            return Response(RecruiterProfileSerializer(instance).data)

        partial = request.method == 'PATCH'
        serializer = RecruiterUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecruiterProfileSerializer(instance).data)


@extend_schema_view(
    # ... `create` uchun schema olib tashlandi
    list=extend_schema(summary="👔 List all staff profiles", tags=["Staff Profiles"]),
    retrieve=extend_schema(summary="👔 Retrieve staff profile", tags=["Staff Profiles"]),
    update=extend_schema(summary="✏️ Update staff profile", tags=["Staff Profiles"]),
    partial_update=extend_schema(summary="📝 Partial update staff profile", tags=["Staff Profiles"]),
    destroy=extend_schema(summary="🗑️ Delete staff profile", tags=["Staff Profiles"]),
)
class StaffProfileViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """
    👔 Staff Profile Management
    """
    queryset = Staff.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'position']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'me']:
            return StaffUpdateSerializer
        return StaffProfileSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return self.queryset.none()
        if user.user_type == 'ADMIN':
            return self.queryset
        elif user.user_type == 'STAFF':
            # Staff faqat o'z profilini ko'rishi yoki barcha stafflarni ko'ra olishi biznes mantiqqa bog'liq
            return self.queryset.filter(user=user) 
        return self.queryset.none()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        try:
            instance = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return Response({'error': 'Staff profili topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            return Response(StaffProfileSerializer(instance).data)

        partial = request.method == 'PATCH'
        serializer = StaffUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StaffProfileSerializer(instance).data)