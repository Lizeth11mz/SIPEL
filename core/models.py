# core/models.py
from django.db import models
from django.contrib.auth.models import User

# Definición actualizada de los Niveles de Acceso
NIVEL_ACCESO_CHOICES = (
    (1, 'Administrador'),
    (2, 'Instructor'),  # 
    (3, 'Estudiante'),          
)

class PerfilUsuario(models.Model):
    """Extiende el modelo User de Django para añadir campos de perfil."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nivel_acceso = models.IntegerField(
        choices=NIVEL_ACCESO_CHOICES, 
        default=3, 
        verbose_name="Nivel de Acceso"
    )
    numero_usuario= models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Número de Usuario"
    )

    def save(self, *args, **kwargs):
        # Si es un objeto nuevo y no tiene número, le asignamos el ID del usuario
        if not self.numero_usuario and self.user_id:
            self.numero_usuario = str(self.user_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.get_nivel_acceso_display()}"