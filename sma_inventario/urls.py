# sma_inventario/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. URLs de la aplicación core (Login/Logout/Index)
    # Al estar aquí, la vista 'index' definida en core/urls.py responderá en http://127.0.0.1:8000/
    path('', include('core.urls')),
    
    # 2. URLs de la aplicación inventario
    # CORRECCIÓN: Se elimina 'namespace=' de aquí porque Django lo detecta automáticamente 
    # gracias al 'app_name' dentro de inventario/urls.py
    path('inventario/', include('inventario.urls')),
    
    # 3. URLs de la aplicación admin_sistema
    # CORRECCIÓN: Se elimina 'namespace=' por la misma razón anterior
    path('administracion/', include('admin_sistema.urls')),
]

# Configuración para servir archivos MEDIA en modo Desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)