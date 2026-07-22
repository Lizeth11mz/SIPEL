from django.contrib import admin
from django.contrib.auth.models import Group, User
from .models import (
    Estudiante, Instructor, Curso, Inscripcion, Evaluacion, Pago, DetallePago,
    AuditoriaEstudiantes, AuditoriaInstructores, AuditoriaCursos, AuditoriaInscripciones,
    AuditoriaEvaluaciones, AuditoriaPagos, AuditoriaDetallePagos,
    ActualizacionEstudiantes, ActualizacionInstructores, ActualizacionCursos, 
    ActualizacionInscripciones, ActualizacionEvaluaciones, ActualizacionPagos, 
    ActualizacionDetallePagos,
    EliminacionEstudiantes, EliminacionInstructores, EliminacionCursos, 
    EliminacionInscripciones, EliminacionEvaluaciones, EliminacionPagos, 
    EliminacionDetallePagos
)

# --- Clase base para tablas de solo lectura ---
class SoloLecturaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_view_permission(self, request, obj=None): return True

# --- Configuración de Instructores ---
@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'especialidad', 'estado')
    
# --- Configuración de Estudiantes ---
@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'email', 'tipo_documento')
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "usuario_auth":
            try:
                grupo = Group.objects.get(name='Estudiante')
                kwargs["queryset"] = grupo.user_set.all()
            except Group.DoesNotExist:
                kwargs["queryset"] = User.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# --- Otros Registros ---
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre_curso', 'categoria', 'costo', 'estado', 'instructor')

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('folio_inscripcion', 'estudiante', 'curso', 'estado', 'total_pago')

@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'calificacion', 'fecha_evaluacion')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'fecha_pago', 'metodo_pago', 'monto')

@admin.register(DetallePago)
class DetallePagoAdmin(admin.ModelAdmin):
    list_display = ('pago', 'concepto', 'cantidad', 'subtotal')

# --- Registro de Tablas de Auditoría ---
@admin.register(AuditoriaEstudiantes, AuditoriaInstructores, AuditoriaCursos, 
                AuditoriaInscripciones, AuditoriaEvaluaciones, AuditoriaPagos, 
                AuditoriaDetallePagos)
class AuditoriaAdmin(SoloLecturaAdmin):
    list_display = ('id_auditoria', 'accion', 'fecha_registro')

# --- Registro de Tablas de Actualización ---
@admin.register(ActualizacionEstudiantes, ActualizacionInstructores, ActualizacionCursos, 
                ActualizacionInscripciones, ActualizacionEvaluaciones, ActualizacionPagos, 
                ActualizacionDetallePagos)
class ActualizacionAdmin(SoloLecturaAdmin):
    list_display = ('id_auditoria', 'fecha_actualizacion')

# --- Registro de Tablas de Eliminación ---
@admin.register(EliminacionEstudiantes, EliminacionInstructores, EliminacionCursos, 
                EliminacionInscripciones, EliminacionEvaluaciones, EliminacionPagos, 
                EliminacionDetallePagos)
class EliminacionAdmin(SoloLecturaAdmin):
    list_display = ('id_auditoria', 'fecha_eliminacion')