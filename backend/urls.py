from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


def api_root(request):
    return JsonResponse({"message": "School-App API"})


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('teacher.urls')),
    path('api/students/', include('student.urls')),
    path('api/homework/', include('homework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)