from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Faqat ADMIN user_type uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.user_type == 'ADMIN'
        )


class IsStaffUser(permissions.BasePermission):
    """Faqat STAFF user_type uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.user_type == 'STAFF'
        )


class IsRecruiterUser(permissions.BasePermission):
    """Faqat RECRUITER user_type uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.user_type == 'RECRUITER'
        )


class IsStudentUser(permissions.BasePermission):
    """Faqat STUDENT user_type uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.user_type == 'STUDENT'
        )


class IsProfileOwner(permissions.BasePermission):
    """O'z profiliga ruxsat berish uchun"""

    def has_object_permission(self, request, view, obj):
        # Agar obj User model bo'lsa
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Agar obj to'g'ridan-to'g'ri User bo'lsa
        return obj == request.user


class CanAccessStudentData(permissions.BasePermission):
    """Student ma'lumotlariga kirish huquqi"""

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.user_type in ['ADMIN', 'STAFF', 'STUDENT']
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin barcha student datalariga kira oladi
        if user.user_type == 'ADMIN':
            return True

        # Staff barcha student datalariga kira oladi
        if user.user_type == 'STAFF':
            return True

        # Student faqat o'z ma'lumotlariga kira oladi
        if user.user_type == 'STUDENT':
            if hasattr(obj, 'user'):
                return obj.user == user
            return obj == user

        return False


class CanAccessOwnProfile(permissions.BasePermission):
    """Faqat o'z profiliga kirish huquqi"""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsAdminOrStaff(permissions.BasePermission):
    """Admin yoki Staff uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.user_type in ['ADMIN', 'STAFF']
        )