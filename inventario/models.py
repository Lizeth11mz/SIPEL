from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import Group

# --- Definición de opciones comunes ---
ESTADO_CHOICES = [
    ('Activo', 'Activo'), ('Inactivo', 'Inactivo'), ('Cancelado', 'Cancelado'),
    ('Pendiente', 'Pendiente'), ('Pagado', 'Pagado'), ('Finalizado', 'Finalizado'),
    ('Activa', 'Activa')
]

# --- Modelos de Escuela (SIPEL) ---
class Estudiante(models.Model):
    estudiante_id = models.AutoField(primary_key=True)
    # Relación uno a uno con el usuario nativo de Django
    usuario_auth = models.OneToOneField(User, on_delete=models.CASCADE, db_column='usuario_id', null=True, blank=True)
    usuario = models.CharField(max_length=50)
    contrasena = models.CharField(max_length=255) 
    nombre_completo = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=150, blank=True, null=True)
    tipo_documento = models.CharField(max_length=20)
    numero_documento = models.CharField(max_length=255) 
    fecha_registro = models.DateTimeField()
    estado = models.CharField(max_length=20, default='Activo', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Estudiantes'

class Instructor(models.Model):
    instructor_id = models.AutoField(primary_key=True)
    usuario_auth = models.OneToOneField(User, on_delete=models.CASCADE, db_column='usuario_id', null=True, blank=True)
    nombre_completo = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=50)
    cedula_profesional = models.CharField(max_length=50) 
    usuario = models.CharField(max_length=50, unique=True)
    contrasena = models.CharField(max_length=128) 
    estado = models.CharField(max_length=20, default='Activo')

    class Meta:
        managed = False
        db_table = 'Instructores'

# --- Señales (Signals) ---

@receiver(post_save, sender=Estudiante)
def crear_user_estudiante(sender, instance, created, **kwargs):
    if created and getattr(instance, 'usuario_auth', None) is None:
        nombres = instance.nombre_completo.split(' ', 1)
        
        # 1. Creamos el usuario en la tabla auth_user incluyendo el email
        user = User.objects.create_user(
            username=instance.usuario,
            password=str(instance.contrasena),
            first_name=nombres[0],
            last_name=nombres[1] if len(nombres) > 1 else "",
            email=getattr(instance, 'email', '')
        )
        
        # 2. Asignamos automáticamente el grupo "Estudiante"
        try:
            grupo_estudiante = Group.objects.get(name='Estudiante')
            user.groups.add(grupo_estudiante)
        except Group.DoesNotExist:
            pass

        # 3. Guardamos la relación de forma segura usando update para evitar bucles con managed = False
        Estudiante.objects.filter(pk=instance.pk).update(usuario_auth=user)

@receiver(post_save, sender=Instructor)
def crear_user_instructor(sender, instance, created, **kwargs):
    if created and getattr(instance, 'usuario_auth', None) is None:
        nombres = instance.nombre_completo.split(' ', 1)
        user = User.objects.create_user(
            username=instance.usuario,
            password=str(instance.contrasena),
            first_name=nombres[0],
            last_name=nombres[1] if len(nombres) > 1 else ""
        )
        
        # Asignamos automáticamente el grupo "Instructor" si existe
        try:
            grupo_instructor = Group.objects.get(name='Instructor')
            user.groups.add(grupo_instructor)
        except Group.DoesNotExist:
            pass

        # Guardamos la relación de forma segura usando update para evitar bucles con managed = False
        Instructor.objects.filter(pk=instance.pk).update(usuario_auth=user)

class Curso(models.Model):
    curso_id = models.AutoField(primary_key=True)
    nombre_curso = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    instructor = models.ForeignKey(Instructor, on_delete=models.DO_NOTHING, db_column='instructor_id')
    duracion_horas = models.IntegerField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activo')
    cupo_maximo = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Cursos'

class Inscripcion(models.Model):
    inscripcion_id = models.AutoField(primary_key=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.DO_NOTHING, db_column='estudiante_id')
    curso = models.ForeignKey(Curso, on_delete=models.DO_NOTHING, db_column='curso_id')
    instructor = models.ForeignKey(Instructor, on_delete=models.DO_NOTHING, db_column='instructor_id')
    folio_inscripcion = models.CharField(max_length=20)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activa')
    total_pago = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'Inscripciones'

class Evaluacion(models.Model):
    evaluacion_id = models.AutoField(primary_key=True)
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.DO_NOTHING, db_column='inscripcion_id')
    calificacion = models.DecimalField(max_digits=5, decimal_places=2)
    comentarios = models.TextField(null=True, blank=True)
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'Evaluaciones'

class Pago(models.Model):
    pago_id = models.AutoField(primary_key=True)
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.DO_NOTHING, db_column='inscripcion_id')
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=30)
    referencia_pago = models.BinaryField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'Pagos'

class DetallePago(models.Model):
    detalle_id = models.AutoField(primary_key=True)
    pago = models.ForeignKey(Pago, on_delete=models.DO_NOTHING, db_column='pago_id')
    concepto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'Detalle_Pagos'

# --- Modelos de Auditoría ---

class AuditoriaEstudiantes(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    estudiante_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Auditoria_Estudiantes'

class AuditoriaInstructores(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    instructor_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Auditoria_Instructores'

class AuditoriaCursos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    curso_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Auditoria_Cursos'

class AuditoriaInscripciones(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    inscripcion_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Auditoria_Inscripciones'

class AuditoriaEvaluaciones(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    evaluacion_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Auditoria_Evaluaciones'

class AuditoriaPagos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    pago_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Auditoria_Pagos'

class AuditoriaDetallePagos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    detalle_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Auditoria_Detalle_Pagos'

# --- Modelos de Actualización ---

class ActualizacionEstudiantes(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    estudiante_id = models.IntegerField()
    usuario_anterior = models.CharField(max_length=50)
    usuario_nuevo = models.CharField(max_length=50)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Actualizacion_Estudiantes'

class ActualizacionInstructores(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    instructor_id = models.IntegerField()
    nombre_completo_anterior = models.CharField(max_length=100)
    nombre_completo_nuevo = models.CharField(max_length=100)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Actualizacion_Instructores'

class ActualizacionCursos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    curso_id = models.IntegerField()
    nombre_curso_anterior = models.CharField(max_length=100)
    nombre_curso_nuevo = models.CharField(max_length=100)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Actualizacion_Cursos'

class ActualizacionInscripciones(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    inscripcion_id = models.IntegerField()
    folio_inscripcion_anterior = models.CharField(max_length=20)
    folio_inscripcion_nuevo = models.CharField(max_length=20)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Actualizacion_Inscripciones'

class ActualizacionEvaluaciones(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    evaluacion_id = models.IntegerField()
    calificacion_anterior = models.DecimalField(max_digits=5, decimal_places=2)
    calificacion_nueva = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Actualizacion_Evaluaciones'

class ActualizacionPagos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    pago_id = models.IntegerField()
    monto_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    monto_nuevo = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Actualizacion_Pagos'

class ActualizacionDetallePagos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    detalle_id = models.IntegerField()
    subtotal_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_nuevo = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Actualizacion_Detalle_Pagos'

# --- Modelos de Eliminación ---

class EliminacionEstudiantes(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    estudiante_id = models.IntegerField()
    fecha_eliminacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Eliminacion_Estudiantes'

class EliminacionInstructores(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    instructor_id = models.IntegerField()
    fecha_eliminacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Eliminacion_Instructores'

class EliminacionCursos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    curso_id = models.IntegerField()
    fecha_eliminacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Eliminacion_Cursos'

class EliminacionInscripciones(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    inscripcion_id = models.IntegerField()
    fecha_eliminacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Eliminacion_Inscripciones'

class EliminacionEvaluaciones(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    evaluacion_id = models.IntegerField()
    fecha_eliminacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Eliminacion_Evaluaciones'

class EliminacionPagos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    pago_id = models.IntegerField()
    fecha_eliminacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Eliminacion_Pagos'

class EliminacionDetallePagos(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    detalle_id = models.IntegerField()
    fecha_eliminacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'Eliminacion_Detalle_Pagos'