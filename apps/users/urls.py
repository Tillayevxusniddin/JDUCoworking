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
    ChangePasswordView
)

router = DefaultRouter(trailing_slash=False)

router.register(r'management', UserManagementViewSet, basename='user-management')
router.register(r'profiles/students', StudentProfileViewSet, basename='student-profiles')
router.register(r'profiles/recruiters', RecruiterProfileViewSet, basename='recruiter-profiles')
router.register(r'profiles/staff', StaffProfileViewSet, basename='staff-profiles')

auth_urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include(auth_urlpatterns)),
]
