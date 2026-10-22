from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.scanner.urls")),
    path("api/v1/", include("apps.messaging.urls")),
]

if settings.ENABLE_API_DOCS:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    ]
