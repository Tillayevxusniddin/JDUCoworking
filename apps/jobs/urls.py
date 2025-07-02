# apps/jobs/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, JobVacancyViewSet, VacancyApplicationViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'jobs', JobViewSet, basename='jobs')
router.register(r'vacancies', JobVacancyViewSet, basename='vacancies')
router.register(r'applications', VacancyApplicationViewSet, basename='applications')

urlpatterns = [
    path('', include(router.urls)),
]
