# apps/jobs/permissions.py
from rest_framework import permissions

class IsApplicantOrStaff(permissions.BasePermission):
    """
    Obyekt egasi (arizachi) yoki Staff/Admin uchun ruxsat.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.user_type in ['STAFF', 'ADMIN']:
            return True
        return obj.applicant == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Faqat ADMIN foydalanuvchilar uchun yozish ruxsatlari.
    Boshqa foydalanuvchilar faqat o'qish ruxsatiga ega.
    """
    def has_permission(self, request, view):
        if request.user.user_type == 'ADMIN':
            return True
        return request.method in permissions.SAFE_METHODS