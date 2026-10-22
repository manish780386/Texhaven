from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.HealthView.as_view()),
    path("config/", views.ConfigView.as_view()),
]
