# apps/reports/permissions.py

from rest_framework import permissions

class IsStudent(permissions.BasePermission):
    """So'rov yuborayotgan foydalanuvchi 'STUDENT' ekanligini tekshiradi."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'STUDENT'

class IsStaffOrAdmin(permissions.BasePermission):
    """So'rov yuborayotgan foydalanuvchi 'STAFF' yoki 'ADMIN' ekanligini tekshiradi."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ['STAFF', 'ADMIN']

class IsOwnerOrStaffAdmin(permissions.BasePermission):
    """
    Obyekt egasi yoki Staff/Admin uchun ruxsat.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'student'):
            # Staff yoki Admin hamma narsani ko'ra oladi
            if request.user.user_type in ['STAFF', 'ADMIN']:
                return True
            # Aks holda, faqat obyekt egasi bo'lsa ruxsat
            return obj.student == request.user
        return False