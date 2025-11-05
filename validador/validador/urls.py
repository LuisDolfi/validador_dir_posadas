# validador/validador/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from validacion import views as vviews
from validacion.views import post_login_redirect, VadiLoginView, LogoutGetView
from validador.core import views
from validador.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", vviews.landing, name="landing"),
    path("validador/", include("validacion.urls")),
    path("api/", include("validador.core.urls")),   # 👈 incluye las rutas de core
    path("validador/chat/", core_views.chat_ui, name="chat_ui"),
    path("dashboard/", views.dashboard, name="dashboard"),


# Auth
    path("accounts/login/", VadiLoginView.as_view(), name="login"),
    path("accounts/logout/", LogoutGetView.as_view(next_page="/"), name="logout"),
]
