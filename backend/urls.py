from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_root(request):
    # Small API index to show available auth endpoints.
    return JsonResponse(
        {
            "message": "School-App API",
            "endpoints": {
                "admin": "/admin/",
                "auth_register": "/api/auth/register/",
                "auth_login": "/api/auth/login/",
                "auth_token_refresh": "/api/auth/token/refresh/",
                "auth_logout": "/api/auth/logout/",
                "auth_me": "/api/auth/me/",
                "teachers": "/api/teachers/",
                "classes": "/api/classes/",
                "timetable": "/api/timetable/",
                "students": "/api/students/",
                "homework": "/api/homework/",
            },
        }
    )


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    # All authentication and account routes live in the accounts app.
    path('api/auth/', include('accounts.urls')),
    path('api/', include('teacher.urls')),
    path('api/student/',  include('student.urls')),
]
