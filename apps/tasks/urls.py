from django.urls import path, include
from rest_framework_nested import routers
from .views import TaskViewSet, TaskCommentViewSet

router = routers.DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='tasks')

tasks_router = routers.NestedDefaultRouter(router, r'tasks', lookup='task')
tasks_router.register(r'comments', TaskCommentViewSet, basename='task-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(tasks_router.urls)),
]