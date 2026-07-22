from django.contrib import admin
from .models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'mostrar_nivel', 'numero_usuario')
    
    # Esto hace que el campo sea visible pero no editable
    readonly_fields = ('numero_usuario',)

    @admin.display(description='Nivel de Acceso')
    def mostrar_nivel(self, obj):
        return obj.get_nivel_acceso_display()