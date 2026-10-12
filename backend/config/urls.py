
from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/demands/", include("demands.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/masterdata/", include("masterdata.urls")),
]
