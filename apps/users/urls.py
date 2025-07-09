# apps/users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    UserManagementViewSet, 
    StudentProfileViewSet, 
    RecruiterProfileViewSet, 
    StaffProfileViewSet,
    # ✅ YANGI IMPORT
    ChangePasswordView
)

router = DefaultRouter(trailing_slash=False)

# Ro'yxatdan o'tkazish
router.register(r'management', UserManagementViewSet, basename='user-management')
router.register(r'profiles/students', StudentProfileViewSet, basename='student-profiles')
router.register(r'profiles/recruiters', RecruiterProfileViewSet, basename='recruiter-profiles')
router.register(r'profiles/staff', StaffProfileViewSet, basename='staff-profiles')

# JWT uchun standart endpointlar
auth_urlpatterns = [
    # 1. Login uchun: email va parol yuboriladi, access va refresh token olinadi
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # 2. Access tokenni yangilash uchun: refresh token yuboriladi, yangi access token olinadi
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 3. Tokenning yaroqliligini tekshirish uchun (ixtiyoriy)
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # 4. Parolni o'zgartirish uchun alohida endpoint
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]

urlpatterns = [
    # Boshqaruv va profillar uchun URL'lar (/users/management/, /users/profiles/...)
    path('', include(router.urls)),
    
    # Autentifikatsiya uchun URL'lar (/users/auth/token/, /users/auth/token/refresh/, ...)
    path('auth/', include(auth_urlpatterns)),
]
