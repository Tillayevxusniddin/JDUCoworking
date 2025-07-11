from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r'workspaces', views.WorkspaceViewSet, basename='workspaces')

urlpatterns = [
    path('', include(router.urls)),
]