# validador/validador/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("validador.core.urls")),   # 👈 incluye las rutas de core
]
