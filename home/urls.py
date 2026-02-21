from django.urls import path
from . import views
from .views import dashboard

urlpatterns = [
    path('', views.index),
    path('dashboard/', dashboard, name='dashboard'),

]
