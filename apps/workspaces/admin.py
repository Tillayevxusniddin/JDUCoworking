# apps/workspaces/admin.py
from django.contrib import admin
from .models import Workspace, WorkspaceMember

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_active', 'workspace_type', 'created_at']
    list_filter = ['is_active', 'workspace_type', 'created_at']
    search_fields = ['name', 'description', 'created_by__email']
    raw_id_fields = ['created_by']
    # Agar koʻp aʼzosi boʻlsa, members bilan koʻrish chogʻida eʼtibor berish mumkin. Misol: Inline qilsa bo'ladi.

@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ['workspace', 'user', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['workspace__name', 'user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['workspace', 'user']
