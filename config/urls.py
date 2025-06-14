from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Digital University Coworking System API",
        default_version='v1',
        description="""
        🎓 **Digital University Coworking System API Documentation**
        
        Bu API universitet talabalarining kovorking faoliyatini boshqarish uchun mo'ljallangan.
        
        ## Asosiy xususiyatlar:
        - 👤 Foydalanuvchilar va rollar boshqaruvi (STUDENT, STAFF, TEAMLEADER, RECRUITER, ADMIN)
        - 🏢 Kovorking maydonlari va a'zolik tizimi
        - 📋 Vazifalar va loyihalar boshqaruvi
        - 📊 Hisobotlar va maosh hisob-kitoblari
        - 🤝 Uchrashuvlar va video konferensiyalar
        - 💼 Ish e'lonlari va ariza berish tizimi
        - 🔔 Bildirishnomalar va xabarlar
        
        ## Autentifikatsiya:
        JWT token orqali autentifikatsiya qilinadi. 
        1. `/api/v1/auth/login/` orqali login qiling
        2. Olgan `access_token` ni `Authorization: Bearer <token>` formatida header ga qo'shing
        3. Token muddati tugaganda `/api/v1/auth/token/refresh/` orqali yangilang
        
        ## User Types:
        - **STUDENT**: Talabalar - vazifalar, hisobotlar, ish izlash
        - **STAFF**: Xodimlar - talabalar bilan ishlash
        - **TEAMLEADER**: Jamoa rahbarlari - loyihalar boshqaruvi
        - **RECRUITER**: Ishga oluvchilar - ish e'lonlari
        - **ADMIN**: Administratorlar - to'liq huquqlar
        
        ## API Endpoints:
        - **Auth**: `/api/v1/auth/` - Autentifikatsiya
        - **Users**: `/api/v1/auth/users/` - Foydalanuvchilar
        - **Workspaces**: `/api/v1/workspaces/` - Kovorking maydonlari
        - **Tasks**: `/api/v1/tasks/` - Vazifalar
        - **Reports**: `/api/v1/reports/` - Hisobotlar
        - **Meetings**: `/api/v1/meetings/` - Uchrashuvlar
        - **Jobs**: `/api/v1/jobs/` - Ish e'lonlari
        - **Notifications**: `/api/v1/notifications/` - Bildirishnomalar
        
        ## Status Codes:
        - **200**: Muvaffaqiyatli
        - **201**: Yaratildi
        - **400**: Noto'g'ri so'rov
        - **401**: Autentifikatsiya kerak
        - **403**: Ruxsat yo'q
        - **404**: Topilmadi
        - **500**: Server xatosi
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(
            name="Development Team",
            email="tillayevx1@gmail.com",
            url="https://github.com/Tillayevxusniddin"
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

def redirect_to_swagger(request):
    return redirect('/swagger/')

urlpatterns = [
    path('', redirect_to_swagger, name='home'),
    path('admin/', admin.site.urls),

    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    path('swagger/', 
         schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', 
         schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),

    # API Endpoints v1
    path('api/v1/auth/', include('apps.users.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass