from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Workspace, WorkspaceMember
from .serializers import WorkspaceSerializer, WorkspaceMemberSerializer, WorkspaceMemberCreateSerializer
from .permissions import IsAdminOrWorkspaceMemberReadOnly, IsAdminUserType

class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAdminOrWorkspaceMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        # Agar swagger fake view bo'lsa, bo'sh queryset
        if getattr(self, 'swagger_fake_view', False):
            return Workspace.objects.none()
        # ADMIN turidagi foydalanuvchi barcha workspace'larni ko'rishi mumkin
        if getattr(user, 'user_type', None) == 'ADMIN':
            return Workspace.objects.all()
        # Boshqa user: faqat a'zosi bo'lgan workspacelar
        return Workspace.objects.filter(members__user=user, members__is_active=True)
    
    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'], url_path='members', permission_classes=[IsAdminOrWorkspaceMemberReadOnly])
    def members(self, request, pk=None):
        """
        GET /workspaces/{pk}/members/:
        - Agar ADMIN bo'lsa yoki workspace a'zosi bo'lsa, a'zolar listi ko'rinadi.
        """
        workspace = get_object_or_404(Workspace, pk=pk)
        self.check_object_permissions(request, workspace)
        members = WorkspaceMember.objects.filter(workspace=workspace)
        serializer = WorkspaceMemberSerializer(members, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['post'], url_path='members', permission_classes=[IsAdminUserType])
    def add_member(self, request, pk=None):
        """
        POST /workspaces/{pk}/members/:
        body: { "user_id": <id>, "role": "MEMBER" (ixtiyoriy), "is_active": true }
        Faol a'zo qo'shish. Faqat ADMIN turidagi user qila oladi.
        """
        workspace = get_object_or_404(Workspace, pk=pk)
        data = {
            'workspace_id': workspace.id,
            'user_id': request.data.get('user_id'),
            'role': request.data.get('role', 'MEMBER'),
            'is_active': request.data.get('is_active', True)
        }
        serializer = WorkspaceMemberCreateSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        member = WorkspaceMember.objects.get(pk=serializer.instance.pk)
        out_ser = WorkspaceMemberSerializer(member)
        return Response(out_ser.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='members/(?P<member_id>[^/.]+)', permission_classes=[IsAdminUserType])
    def remove_member(self, request, pk=None, member_id=None):
        """
        DELETE /workspaces/{pk}/members/{member_id}/:
        Faqat ADMIN turidagi foydalanuvchi a'zoni olib tashlashi mumkin.
        """
        workspace = get_object_or_404(Workspace, pk=pk)
        member = get_object_or_404(WorkspaceMember, pk=member_id, workspace=workspace)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)









