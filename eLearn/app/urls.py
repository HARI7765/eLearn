from django.urls import path
from . import views  # Import views from current directory

urlpatterns = [
    path('', views.home, name='home'),
]