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

        # 2. Verificamos si es Estudiante o Instructor para extraer su contraseña binaria
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

        # 3. Validar la contraseña según el algoritmo con el que fue cifrada en tu BD de SQL Server.
        # NOTA: Aquí debes aplicar la misma lógica matemática o función hash con la que se cifró 
        # originalmente la contraseña en la base de datos para compararla con el 'password' en texto plano ingresado.
        # Por ejemplo, si se cifró usando SHA-256 o MD5 en SQL:
        
        # Ejemplo si fuera SHA256 (ajusta según el algoritmo exacto que usaste en SQL):
        password_ingresada_hash = hashlib.sha256(password.encode('utf-8')).digest()
        
        if contrasena_binaria == password_ingresada_hash:
            return user
            
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None