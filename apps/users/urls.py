from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'users', views.UserManagementViewSet, basename='users')
router.register(r'profiles/students', views.StudentProfileViewSet, basename='student-profiles')
router.register(r'profiles/recruiters', views.RecruiterProfileViewSet, basename='recruiter-profiles')
router.register(r'profiles/staff', views.StaffProfileViewSet, basename='staff-profiles')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]