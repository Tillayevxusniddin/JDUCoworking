from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """Faqat 'ADMIN' turidagi foydalanuvchilar uchun ruxsat."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'ADMIN'

class IsStaffUser(permissions.BasePermission):
    """Faqat 'STAFF' turidagi foydalanuvchilar uchun ruxsat."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'STAFF'

class IsRecruiterUser(permissions.BasePermission):
    """Faqat 'RECRUITER' turidagi foydalanuvchilar uchun ruxsat."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'RECRUITER'

class IsStudentUser(permissions.BasePermission):
    """Faqat 'STUDENT' turidagi foydalanuvchilar uchun ruxsat."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'STUDENT'

class IsAdminOrStaff(permissions.BasePermission):
    """Faqat 'ADMIN' yoki 'STAFF' turidagi foydalanuvchilar uchun ruxsat."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ['ADMIN', 'STAFF']

class IsProfileOwner(permissions.BasePermission):
    """Obyekt egasi yoki Admin uchun ruxsat."""
    def has_object_permission(self, request, view, obj):
        # Admin barcha obyektlarga kira oladi
        if request.user.user_type == 'ADMIN':
            return True
        
        # User modelini tekshirish
        if isinstance(obj, request.user.__class__):
            return obj == request.user
            
        # Profil modellarini (Student, Staff, Recruiter) tekshirish
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False