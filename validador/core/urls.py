# validador/core/urls.py
from django.urls import path
from .views import api_validate, test_view

urlpatterns = [
    path("api/validate/", api_validate, name="api_validate"),
    path("test/", test_view, name="test_view"),
]
