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
    list=extend_schema(summary="Ish maydonlari ro'yxati"),
    retrieve=extend_schema(summary="Bitta ish maydoni ma'lumotlari"),
    update=extend_schema(summary="[ADMIN] Ish maydonini tahrirlash"),
    partial_update=extend_schema(summary="[ADMIN] Ish maydonini qisman tahrirlash"),
    destroy=extend_schema(summary="[ADMIN] Ish maydonini o'chirish"),
    add_member=extend_schema(
        summary="[ADMIN] Ish maydoniga a'zo qo'shish",
        request=WorkspaceMemberCreateSerializer, # To'g'ri serializer ko'rsatildi
        responses={201: WorkspaceMemberDetailSerializer} # Yangi a'zolik ma'lumotlari qaytariladi
    ),
    members=extend_schema(summary="Ish maydoni a'zolari ro'yxati"),
)
class WorkspaceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    """
    Ish maydonlarini boshqarish uchun.
    Yangi ish maydoni faqat 'Job' yaratilganda avtomatik hosil qilinadi.
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
        # `update`, `partial_update` uchun default
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

    # --- MANA SHU BLOK MUHIM ---
    @extend_schema(
        summary="[ADMIN] Ish maydoni a'zosini o'chirish",
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Workspace ID'),
            OpenApiParameter(name='member_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="A'zolik ID raqami (WorkspaceMember'ning ID'si)")
        ]
    )
    # ---------------------------
    @action(detail=True, methods=['delete'], url_path='remove-member/(?P<member_id>[^/.]+)', permission_classes=[IsAdminUserType])
    def remove_member(self, request, pk=None, member_id=None):
        workspace = get_object_or_404(Workspace, pk=pk)
        member = get_object_or_404(WorkspaceMember, pk=member_id, workspace=workspace)
        if member.role == 'ADMIN' and workspace.members.filter(role='ADMIN').count() == 1:
            return Response(
                {"error": "Ish maydonidagi oxirgi adminni o'chirib bo'lmaydi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    @extend_schema(
        summary="[STAFF/ADMIN] A'zoning shaxsiy stavkasini o'zgartirish",
        request=WorkspaceMemberRateUpdateSerializer,
        parameters=[
        OpenApiParameter(name='pk', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Workspace ID'),
        OpenApiParameter(name='member_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="A'zolik ID raqami")
        ]
    )
    @action(
        detail=True, 
        methods=['patch'], 
        url_path='members/(?P<member_id>[^/.]+)/update-rate', 
        permission_classes=[IsAdminOrStaff] # Staff yoki Admin o'zgartira oladi
    )
    def update_member_rate(self, request, pk=None, member_id=None):
        """A'zoning shaxsiy soatbay stavkasini o'zgartirish."""
        member = get_object_or_404(WorkspaceMember, pk=member_id, workspace_id=pk)
        serializer = WorkspaceMemberRateUpdateSerializer(instance=member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(WorkspaceMemberDetailSerializer(member).data)