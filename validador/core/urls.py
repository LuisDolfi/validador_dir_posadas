# validador/core/urls.py
#from .views import api_validate, test_view
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import QueryLogViewSet
from validador.core import views, api

app_name = 'validador.core'

router = DefaultRouter()
router.register(r"addresses", QueryLogViewSet, basename="addresses")

urlpatterns = [
    path("", include(router.urls)),
    path("chat/", api.chat, name="chat_vadi"),
    path("validador/core/", views.chat_ui, name="chat_ui"),
    path("querylogs/", views.querylog_list, name="querylog_list"),
    path("querylogs/<int:pk>/", views.querylog_detail, name="querylog_detail"),
    path("querylogs/<int:pk>/delete/", views.querylog_delete, name="querylog_delete"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("heatmap_data/", views.heatmap_data, name="heatmap_data"),


    #path("ask/", api.ask_vadi, name="ask_vadi"),
    #path("api/validate/", api_validate, name="api_validate"),
    #path("test/", test_view, name="test_view"),
]
