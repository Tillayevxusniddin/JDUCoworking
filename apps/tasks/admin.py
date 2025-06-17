from django.contrib import admin
from .models import Task, TaskComment

class TaskCommentInline(admin.TabularInline):
    """Vazifa sahifasida izohlarni ko'rsatish va tahrirlash uchun inline."""
    model = TaskComment
    extra = 1
    readonly_fields = ('user', 'created_at')
    raw_id_fields = ('user',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'created_by', 'status', 'priority', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'due_date')
    search_fields = ('title', 'description', 'assigned_to__email', 'created_by__email')
    raw_id_fields = ('assigned_to', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    inlines = [TaskCommentInline]

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment', 'task__title', 'user__email')
    raw_id_fields = ('task', 'user')