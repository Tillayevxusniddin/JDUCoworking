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
        description="Create new workspace (Admin only)",
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
        serializer.save(created_by=self.request.user)

    @extend_schema(
        summary="List workspace members",
        description="Get list of all members in a workspace",
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workspace ID'
            )
        ],
        responses={
            200: WorkspaceMemberSerializer(many=True),
            403: OpenApiResponse(description="Forbidden if not member or admin"),
            404: OpenApiResponse(description="Workspace not found")
        },
        examples=[
            OpenApiExample(
                'Example response',
                value=[{
                    "id": 1,
                    "user": {"id": 1, "email": "user@example.com"},
                    "role": "ADMIN",
                    "is_active": True
                }],
                response_only=True
            )
        ]
    )
    @action(detail=True, methods=['get'], url_path='members', permission_classes=[IsAdminOrWorkspaceMemberReadOnly])
    def members(self, request, pk=None):
        workspace = get_object_or_404(Workspace, pk=pk)
        self.check_object_permissions(request, workspace)
        members = WorkspaceMember.objects.filter(workspace=workspace)
        serializer = WorkspaceMemberSerializer(members, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Add member to workspace",
        description="Add new member to workspace (Admin only)",
        request=WorkspaceMemberCreateSerializer,
        responses={
            201: WorkspaceMemberSerializer,
            400: OpenApiResponse(description="Bad request if validation fails"),
            403: OpenApiResponse(description="Forbidden if not admin"),
            404: OpenApiResponse(description="Workspace not found")
        },
        examples=[
            OpenApiExample(
                'Example request',
                value={
                    "user_id": 2,
                    "role": "MEMBER",
                    "is_active": True
                },
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['post'], url_path='add-member', permission_classes=[IsAdminUserType])
    def add_member(self, request, pk=None):
        workspace = get_object_or_404(Workspace, pk=pk)
        data = {
            'workspace_id': workspace.id,
            'user_id': request.data.get('user_id'),
            'role': request.data.get('role', 'MEMBER'),
            'is_active': request.data.get('is_active', True)
        }
        serializer = WorkspaceMemberCreateSerializer(data=data, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        member = serializer.instance
        out_ser = WorkspaceMemberSerializer(member)
        return Response(out_ser.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Remove member from workspace",
        description="Remove member from workspace (Admin only)",
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workspace ID'
            ),
            OpenApiParameter(
                name='member_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Member ID to remove'
            )
        ],
        responses={
            204: OpenApiResponse(description="No content"),
            403: OpenApiResponse(description="Forbidden if not admin"),
            404: OpenApiResponse(description="Workspace or member not found")
        }
    )
    @action(detail=True, methods=['delete'], url_path='remove-member/(?P<member_id>[^/.]+)', permission_classes=[IsAdminUserType])
    def remove_member(self, request, pk=None, member_id=None):
        workspace = get_object_or_404(Workspace, pk=pk)
        member = get_object_or_404(WorkspaceMember, pk=member_id, workspace=workspace)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)