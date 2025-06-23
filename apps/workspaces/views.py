# apps/workspaces/views.py

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes, OpenApiExample, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Workspace, WorkspaceMember
from .serializers import WorkspaceSerializer, WorkspaceMemberSerializer, WorkspaceMemberCreateSerializer
from .permissions import IsAdminOrWorkspaceMemberReadOnly, IsAdminUserType

@extend_schema_view(
    list=extend_schema(
        summary="List workspaces",
        description="Get list of workspaces accessible to current user",
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
            OpenApiParameter(
                name='workspace_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by workspace type (GENERAL, PROJECT, STUDY, MEETING)'
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Retrieve workspace",
        description="Get workspace details by ID"
    ),
    create=extend_schema(
        summary="Create workspace",
        description="Create new workspace. The creator is automatically added as an Admin member. (Admin only)",
        request=WorkspaceSerializer,
        responses={
            201: WorkspaceSerializer,
            403: OpenApiResponse(description="Forbidden if not admin")
        }
    ),
    update=extend_schema(
        summary="Update workspace",
        description="Full update workspace (Admin only)",
        request=WorkspaceSerializer,
        responses={
            200: WorkspaceSerializer,
            403: OpenApiResponse(description="Forbidden if not admin")
        }
    ),
    partial_update=extend_schema(
        summary="Partial update workspace",
        description="Partial update workspace (Admin only)",
        request=WorkspaceSerializer,
        responses={
            200: WorkspaceSerializer,
            403: OpenApiResponse(description="Forbidden if not admin")
        }
    ),
    destroy=extend_schema(
        summary="Delete workspace",
        description="Delete workspace (Admin only)",
        responses={
            204: OpenApiResponse(description="No content"),
            403: OpenApiResponse(description="Forbidden if not admin")
        }
    ),
    add_member=extend_schema(
        summary="Add member to workspace",
        description="Add a new member to a workspace. The role is assigned automatically based on the user's global type (e.g., STUDENT, STAFF) and status (e.g., TEAMLEAD). (Admin only)",
        request=WorkspaceMemberCreateSerializer,
        responses={ 201: WorkspaceMemberSerializer, }
    ),
    members=extend_schema(
        summary="List workspace members",
        description="Get a list of all members in a specific workspace."
    ),
    remove_member=extend_schema(
        summary="Remove member from workspace",
        description="Remove a specific member from a workspace. (Admin only)"
    )
)
class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAdminOrWorkspaceMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return Workspace.objects.none()
        if not user.is_authenticated:
            return Workspace.objects.none()
        if getattr(user, 'user_type', None) == 'ADMIN':
            return Workspace.objects.all()
        return Workspace.objects.filter(members__user=user, members__is_active=True)
    
    def perform_create(self, serializer):
        """
        Creates a new workspace and automatically adds the creator as a member with the 'ADMIN' role.
        """
        workspace = serializer.save(created_by=self.request.user)
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=self.request.user,
            role='ADMIN'
        )

    @action(detail=True, methods=['get'], url_path='members', permission_classes=[IsAdminOrWorkspaceMemberReadOnly])
    def members(self, request, pk=None):
        """
        Retrieves and returns all members of a specific workspace.
        """
        workspace = get_object_or_404(Workspace, pk=pk)
        self.check_object_permissions(request, workspace) # Check if user can view this workspace
        members = WorkspaceMember.objects.filter(workspace=workspace)
        serializer = WorkspaceMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-member', permission_classes=[IsAdminUserType])
    def add_member(self, request, pk=None):
        """
        Adds a user to the workspace. The role is determined automatically by the serializer.
        """
        serializer = WorkspaceMemberCreateSerializer(
            data=request.data, 
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        
        # Use the detailed serializer for the response
        output_serializer = WorkspaceMemberSerializer(member)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='remove-member/(?P<member_id>[^/.]+)', permission_classes=[IsAdminUserType])
    def remove_member(self, request, pk=None, member_id=None):
        """
        Removes a member from the workspace.
        """
        workspace = get_object_or_404(Workspace, pk=pk)
        member = get_object_or_404(WorkspaceMember, pk=member_id, workspace=workspace)
        
        # Prevent the last admin from being removed (optional but good practice)
        if member.role == 'ADMIN' and workspace.members.filter(role='ADMIN').count() == 1:
            return Response(
                {"error": "Cannot remove the last admin from the workspace."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)