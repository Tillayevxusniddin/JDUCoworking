# apps/tasks/permissions.py

from rest_framework import permissions
from apps.workspaces.models import WorkspaceMember

def get_user_role_in_workspace(user, workspace):
    """Get the role of a user in a specific workspace."""
    try:
        return WorkspaceMember.objects.get(workspace=workspace, user=user).role
    except WorkspaceMember.DoesNotExist:
        return None

class IsWorkspaceMember(permissions.BasePermission):
    """Checks if the user is an active member of the workspace associated with the task."""
    message = "You must be a member of the workspace to perform this action."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.user_type == 'ADMIN':
            return True
        return WorkspaceMember.objects.filter(workspace=obj.workspace, user=user, is_active=True).exists()

class IsTeamLeaderForAction(permissions.BasePermission):
    """
    Checks if the user is the team leader of the workspace associated with the task.
    """
    message = "You must be a team leader of the workspace to perform this action."

    def has_permission(self, request, view):
        """
        General permission check. Primarily used for 'create'.
        For other actions, the check is passed to has_object_permission.
        """
        user = request.user
        if not user.is_authenticated:
            return False

        if view.action == 'create':
            workspace_id = request.data.get('workspace')
            if not workspace_id:
                self.message = "Workspace ID must be provided to create a task."
                return False
            
            role = get_user_role_in_workspace(user, workspace_id)
            return role == 'TEAMLEADER'
        return True

    def has_object_permission(self, request, view, obj):
        """ Check if the user is the team leader of the workspace associated with the task."""
        user = request.user
        role = get_user_role_in_workspace(user, obj.workspace)

        return obj.created_by == user and role == 'TEAMLEADER'

class IsAssigneeForStatusUpdate(permissions.BasePermission):
    """Only allows the assignee of the task to change its status."""
    message = "Only the assignee of the task can change its status."

    def has_object_permission(self, request, view, obj):
        return obj.assigned_to == request.user

class IsCommentOwner(permissions.BasePermission):
    """Checks if the user is the owner of the comment."""
    message = "Only the owner of the comment can modify or delete it."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user