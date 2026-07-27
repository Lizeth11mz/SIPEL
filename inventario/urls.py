# inventario/urls.py
from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # --- VISTAS POR ROL (Registros) ---
    path('registros/', views.home_registros, name='registros'),
    path('registros/estudiante/', views.registros_estudiante, name='registros_estudiante'),
    path('registros/instructor/', views.registros_instructor, name='registros_instructor'),

    # --- PANEL DEL INSTRUCTOR ---
    path('instructor/mis-cursos/', views.mis_cursos, name='mis_cursos'),
    path('instructor/estudiantes/', views.lista_estudiantes, name='lista_estudiantes'),
    path('instructor/evaluar/', views.evaluar_alumnos, name='evaluar_alumnos'),
    path('instructor/evaluar/nota/<int:inscripcion_id>/', views.registrar_nota, name='registrar_nota'),
    
    # --- GESTIÓN INSTRUCTORES ---
    path('instructores/', views.gestion_instructores, name='gestion_instructores'),
    path('instructores/crear/', views.crear_instructor, name='crear_instructor'),
    path('instructores/editar/<int:instructor_id>/', views.editar_instructor, name='editar_instructor'),
    path('instructores/eliminar/<int:instructor_id>/', views.eliminar_instructor, name='eliminar_instructor'),
    
    # --- ESTUDIANTES ---
    path('estudiantes/', views.gestion_estudiantes, name='gestion_estudiantes'),
    path('estudiantes/crear/', views.crear_estudiantes, name='crear_estudiantes'),
    path('estudiantes/editar/<int:estudiante_id>/', views.editar_estudiante, name='editar_estudiante'),
    path('estudiantes/eliminar/<int:estudiante_id>/', views.eliminar_estudiante, name='eliminar_estudiante'),
    
    # --- CURSOS ---
    path('cursos/', views.gestion_cursos, name='gestion_cursos'),
    path('cursos/crear/', views.crear_curso, name='crear_curso'),
    path('cursos/editar/<int:curso_id>/', views.editar_curso, name='editar_curso'),
    path('cursos/eliminar/<int:curso_id>/', views.eliminar_curso, name='eliminar_curso'),
    
    # --- INSCRIPCIONES ---
    path('inscripciones/', views.gestion_inscripciones, name='gestion_inscripciones'),
    path('inscripciones/crear/', views.crear_inscripciones, name='crear_inscripciones'),
    path('inscripciones/editar/<int:inscripcion_id>/', views.editar_inscripcion, name='editar_inscripcion'),
    path('inscripciones/eliminar/<int:inscripcion_id>/', views.eliminar_inscripcion, name='eliminar_inscripcion'),

    # --- GESTIÓN GENERAL ---
    path('pagos/', views.gestion_pagos, name='gestion_pagos'),
    
    # --- REPORTES Y EVALUACIONES ---
    path('evaluaciones/', views.gestion_evaluaciones, name='gestion_evaluaciones'),
    path('evaluaciones/editar/<int:pk>/', views.editar_evaluacion, name='editar_evaluacion'),
path('evaluaciones/eliminar/<int:pk>/', views.eliminar_evaluacion, name='eliminar_evaluacion'),
    path('reportes/', views.reportes_view, name='reportes'),
    
    # --- GESTIÓN USUARIOS ---
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/cambiar-contrasena/<int:user_id>/', views.cambiar_contrasena_usuario, name='cambiar_contrasena_usuario'),
    # --- LOGOUT ---
    path('logout/', views.custom_logout_view, name='logout'),


    #--------------path('estudiante/cmaterias,pagos,incripciones -----
    path('estudiante/mis_materias/', views.mis_materias,name='mis_materias'),
    path('estudiante/inscripciones/', views.mis_inscripciones, name='mis_inscripciones'),
   path('estudiante/inscribirme/', views.inscribir_curso, name='inscribir_curso'),
    path('estudiante/evaluaciones/', views.mis_evaluaciones, name='mis_evaluaciones'),
    path('estudiante/pagos/', views.mis_pagos, name='mis_pagos'),
    path('estudiante/pagos/descargar/<int:pago_id>/', views.descargar_comprobante_pdf, name='descargar_comprobante_pdf'),
]