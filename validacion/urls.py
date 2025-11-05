from django.urls import path
from .views import ValidateAddress
from . import views


app_name = "validacion"

urlpatterns = [
    path("", views.validador_usuario, name="usuario"),
    path("historial/", views.historial, name="historial"),
    path("validate_address", ValidateAddress.as_view(), name="validate_address"),
]