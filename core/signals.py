# C:\Users\ADMIN\Desktop\proyecto\sma_orler\core\signals.py

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import PerfilUsuario 
from django.core.exceptions import ObjectDoesNotExist

# COMENTA ESTA LÍNEA TEMPORALMENTE PARA LA PRUEBA DE DIAGNÓSTICO.
# Esto evita que el código interno se ejecute en cada login.
# @receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Crea un PerfilUsuario cuando un User es creado. 
       Intenta guardar el perfil existente si el User es actualizado."""
    
    # 1. Crear el perfil para un usuario nuevo
    if created:
        try:
            PerfilUsuario.objects.create(user=instance)
        except Exception as e:
            # En un entorno de producción, usa logging, no print
            print(f"Error crítico al crear PerfilUsuario para {instance.username}: {e}")
            return # Evita intentar guardar si la creación falló

    # 2. Guardar el perfil existente para un usuario actualizado
    # ESTO SE EJECUTA EN CADA LOGIN (y es la fuente de la lentitud si el .save() es pesado)
    try:
        instance.perfilusuario.save()
    except ObjectDoesNotExist:
        # Si el perfil no existe, intenta crearlo (como fallback)
        pass 
    except Exception as e:
        print(f"Error al guardar PerfilUsuario para {instance.username}: {e}")

