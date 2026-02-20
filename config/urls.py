"""URL configuration for config project."""
from importlib import import_module

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def _missing_app_view(_request, *args, **kwargs):
    return JsonResponse(
        {
            "detail": "Requested module is unavailable in this prototype snapshot.",
            "status": "service_unavailable",
        },
        status=503,
    )


def _safe_include(module_path):
    try:
        import_module(module_path)
        return include(module_path)
    except ModuleNotFoundError:
        fallback_patterns = [path('', _missing_app_view, name='module_unavailable')]
        return include((fallback_patterns, 'fallback'))


urlpatterns = [
    path('', lambda request: JsonResponse({"message": "Knowledge Platform API 🚀"})),
    path('admin/', admin.site.urls),
    path('api/users/', _safe_include('apps.users.urls')),
    path('api/workspaces/', _safe_include('apps.workspaces.urls')),
    path('api/articles/', _safe_include('apps.articles.urls')),
    path('api/approvals/', _safe_include('apps.approvals.urls')),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', _safe_include('apps.users.urls')),
]
