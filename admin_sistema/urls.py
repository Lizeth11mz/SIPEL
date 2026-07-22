# admin_sistema/urls.py

from django.urls import path
from . import views

# Namespace para usar: {% url 'admin_sistema:nombre' %}
app_name = 'admin_sistema'

urlpatterns = [

    # ============================
    # 1) LOGIN SEGÚN TIPO DE USUARIO
    # ============================

    path('admin/login/', views.login_admin, name='login_admin'),
    path('almacen/login/', views.login_warehouse, name='login_warehouse'),
    path('usuario/login/', views.login_user, name='login_user'),


   
    # ============================
    # 3) REPORTES
    # ============================
    
    # Esta ruta permitirá acceder a la vista de reportes
    path('reportes/', views.generar_reportes, name='reportes'),
]