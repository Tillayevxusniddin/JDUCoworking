# apps/meetings/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeetingViewSet, MeetingAttendeeViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'meetings', MeetingViewSet, basename='meetings')
router.register(r'attendees', MeetingAttendeeViewSet, basename='attendees')



urlpatterns = [
    path('', include(router.urls)),
]