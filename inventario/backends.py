from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import Estudiante, Instructor
import hashlib

class BinaryPasswordBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 1. Buscamos el usuario en auth_user
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        # 2. SI ES ADMINISTRADOR / STAFF / SUPERUSUARIO:
        # Validamos directamente con el método nativo de Django (check_password) 
        # y evitamos buscar en Estudiantes o Instructores.
        if user.is_staff or user.is_superuser:
            if user.check_password(password):
                return user
            return None

        # 3. SI ES UN ESTUDIANTE O INSTRUCTOR (Manejo de contraseña binaria)
        contrasena_binaria = None
        
        # Intentar buscar en Estudiantes
        estudiante = Estudiante.objects.filter(usuario_auth=user).first()
        if estudiante:
            contrasena_binaria = estudiante.contrasena
        else:
            # Intentar buscar en Instructores
            instructor = Instructor.objects.filter(usuario_auth=user).first()
            if instructor:
                contrasena_binaria = instructor.contrasena

        if not contrasena_binaria:
            return None

        # 4. Validar la contraseña binaria ingresada
        password_ingresada_hash = hashlib.sha256(password.encode('utf-8')).digest()
        
        if contrasena_binaria == password_ingresada_hash:
            return user
            
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None