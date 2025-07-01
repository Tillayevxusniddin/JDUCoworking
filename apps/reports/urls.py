# apps/reports/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailyReportViewSet, MonthlyReportViewSet, SalaryViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'daily-reports', DailyReportViewSet, basename='daily-reports')
router.register(r'monthly-reports', MonthlyReportViewSet, basename='monthly-reports')
router.register(r'salaries', SalaryViewSet, basename='salaries')

urlpatterns = [
    path('', include(router.urls)),
]