from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, 
    UserManagementViewSet, 
    StudentProfileViewSet, 
    RecruiterProfileViewSet, 
    StaffProfileViewSet
)

# `trailing_slash=False` URL'lar oxirida slesh bo'lmasligini ta'minlaydi (masalan, /users/auth/login)
router = DefaultRouter(trailing_slash=False)

# Ro'yxatdan o'tkazish
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'management', UserManagementViewSet, basename='user-management')
router.register(r'profiles/students', StudentProfileViewSet, basename='student-profiles')
router.register(r'profiles/recruiters', RecruiterProfileViewSet, basename='recruiter-profiles')
router.register(r'profiles/staff', StaffProfileViewSet, basename='staff-profiles')

urlpatterns = [
    # Router tomonidan generatsiya qilingan barcha URL'larni qo'shish
    # URL'lar /users/ prefiksi bilan boshlanadi (asosiy urls.py faylidan)
    path('', include(router.urls)),
]