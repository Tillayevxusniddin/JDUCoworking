# apps/workspaces/views.py

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Workspace, WorkspaceMember
from .serializers import (
    WorkspaceListSerializer, WorkspaceDetailSerializer, 
    WorkspaceMemberListSerializer, WorkspaceMemberDetailSerializer,
    WorkspaceMemberCreateSerializer, WorkspaceMemberRateUpdateSerializer
)
from .permissions import IsAdminOrWorkspaceMemberReadOnly, IsAdminUserType, IsWorkspaceMembersStaff
from apps.users.permissions import IsAdminOrStaff

@extend_schema_view(
    list=extend_schema(summary="Workspace lists"),
    retrieve=extend_schema(summary="Workspace details"),
    update=extend_schema(summary="[ADMIN] Update workspace"),
    partial_update=extend_schema(summary="[ADMIN] Partial update workspace"),
    destroy=extend_schema(summary="[ADMIN] Delete workspace"),
    add_member=extend_schema(
        summary="[ADMIN] Add member to workspace",
        request=WorkspaceMemberCreateSerializer, 
        responses={201: WorkspaceMemberDetailSerializer}
    ),
    members=extend_schema(summary="Workspace members list"),
)
class WorkspaceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    """
    Workspace management.
    A new workspace is automatically created only when a 'Job' is created.
    """
    permission_classes = [IsAdminOrWorkspaceMemberReadOnly]
    def get_serializer_class(self):
        if self.action == 'list':
            return WorkspaceListSerializer
        if self.action == 'retrieve':
            return WorkspaceDetailSerializer
        if self.action == 'members':
            return WorkspaceMemberListSerializer
        if self.action == 'add_member':
            return WorkspaceMemberCreateSerializer
        if self.action == 'update_member_rate':
            return WorkspaceMemberRateUpdateSerializer
        return WorkspaceDetailSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Workspace.objects.none()
        user = self.request.user
        if not user.is_authenticated:
            return Workspace.objects.none()
        if getattr(user, 'user_type', None) == 'ADMIN':
            return Workspace.objects.all()
        return Workspace.objects.filter(members__user=user, members__is_active=True)

    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        workspace = self.get_object()
        self.check_object_permissions(request, workspace)
        members = WorkspaceMember.objects.filter(workspace=workspace)
        serializer = self.get_serializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        serializer = self.get_serializer(
            data=request.data, 
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        output_serializer = WorkspaceMemberDetailSerializer(member)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="[ADMIN] Remove member from workspace",
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Workspace ID'),
            OpenApiParameter(name='member_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="Membership ID (WorkspaceMember's ID)")
        ]
    )
    @action(detail=True, methods=['delete'], url_path='remove-member/(?P<member_id>[^/.]+)', permission_classes=[IsAdminUserType])
    def remove_member(self, request, pk=None, member_id=None):
        workspace = get_object_or_404(Workspace, pk=pk)
        member = get_object_or_404(WorkspaceMember, pk=member_id, workspace=workspace)
        if member.role == 'ADMIN' and workspace.members.filter(role='ADMIN').count() == 1:
            return Response(
                {"error": "You cannot remove the last admin from the workspace."},
                status=status.HTTP_400_BAD_REQUEST
            )
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    @extend_schema(
        summary="[STAFF/ADMIN] Update member's personal rate",
        request=WorkspaceMemberRateUpdateSerializer,
        parameters=[
        OpenApiParameter(name='pk', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Workspace ID'),
        OpenApiParameter(name='member_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="Membership ID")
        ]
    )
    @action(
        detail=True, 
        methods=['patch'], 
        url_path='members/(?P<member_id>[^/.]+)/update-rate', 
        permission_classes=[IsAdminOrStaff] 
    )
    def update_member_rate(self, request, pk=None, member_id=None):
        """Update member's personal hourly rate."""
        member = get_object_or_404(WorkspaceMember, pk=member_id, workspace_id=pk)
        serializer = WorkspaceMemberRateUpdateSerializer(instance=member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(WorkspaceMemberDetailSerializer(member).data)