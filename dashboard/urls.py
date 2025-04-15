from django.urls import path
from . import views
from .views import fetch_data_api

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('fetch-data-api/', fetch_data_api, name='fetch_data_api'),
]
