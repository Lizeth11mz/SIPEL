# core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ====================================
    # 1. VISTAS PÚBLICAS
    # ====================================
    path('', views.index, name='index'),
    path('bienvenido/', views.bienvenido, name='bienvenido'),
    path('acerca-de/', views.acerca_de, name='acerca_de'),
    path('servicios/', views.servicios, name='servicios'),
    path('contacto/', views.contacto, name='contacto'),

    # ====================================
    # 2. AUTENTICACIÓN
    # ====================================
    # Se cambió auth_views.LoginView por tu función personalizada:
    path('login/', views.login_view, name='login'),
    
    path('logout/', views.custom_logout_view, name='logout'),

    # ====================================
    # 3. REGISTROS
    # ====================================
    path('registros/', views.home_registros, name='registros'),
]