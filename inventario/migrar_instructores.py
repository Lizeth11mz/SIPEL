import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SIPEL.settings') # Cambia 'SIPEL' por el nombre de tu proyecto si es diferente
django.setup()

from django.contrib.auth.models import User, Group
from inventario.models import Instructor
from django.db import connection

grupo_instructor, _ = Group.objects.get_or_create(name='Instructor')

with connection.cursor() as cursor:
    cursor.execute("SELECT instructor_id, usuario, email, nombre_completo, contrasena FROM Instructores WHERE usuario_id IS NULL")
    filas = cursor.fetchall()

print(f"Instructores pendientes encontrados: {len(filas)}")

for fila in filas:
    inst_id, username, email, nombre_completo, contrasena = fila
    if username and email:
        raw_pass = "PasswordPorDefecto123"
        if contrasena:
            if isinstance(contrasena, bytes):
                try:
                    raw_pass = contrasena.decode('utf-8')
                except:
                    pass
            else:
                raw_pass = str(contrasena)

        user = User(
            username=username,
            email=email,
            first_name=nombre_completo.split(' ')[0] if nombre_completo else ""
        )
        user.set_password(raw_pass)
        user.save()
        user.groups.add(grupo_instructor)

        inst = Instructor.objects.get(pk=inst_id)
        inst.usuario_auth = user
        if inst.contrasena and not isinstance(inst.contrasena, bytes):
            inst.contrasena = str(inst.contrasena).encode('utf-8')
        super(Instructor, inst).save()
        
        print(f"Instructor migrado correctamente: {nombre_completo}")

print("¡Migración de instructores finalizada con éxito!")