# inventario/views.py
print("--- LEYENDO EL ARCHIVO VIEWS.PY CORRECTO ---")
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Q
from django.db import transaction 
from core.decorators import role_required 
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum

from .utils import cifrar_dato
from .models import Estudiante, Curso, Inscripcion, Pago, Instructor, Evaluacion
from .forms import EstudianteForm, CursoForm, InstructorForm, InscripcionForm

# --- VISTAS POR ROL ---
@login_required
@role_required(allowed_roles=['Estudiante'])
def registros_estudiante(request):
    return render(request, 'inventario/registros_estudiante.html')

@login_required
@role_required(allowed_roles=['Instructor'])
def registros_instructor(request):
    return render(request, 'inventario/registros_instructor.html')

# --- VISTA PRINCIPAL REGISTROS ---
@login_required
def home_registros(request):
    return render(request, 'inventario/registros.html')

# --- VISTAS PARA INSTRUCTOR ---
@login_required
@role_required(allowed_roles=['Instructor'])
def mis_cursos(request):
    cursos = Curso.objects.filter(instructor__usuario=request.user)
    return render(request, 'inventario/mis_cursos.html', {'mis_cursos': cursos})

@login_required
@role_required(allowed_roles=['Instructor'])
def lista_estudiantes(request):
    inscripciones = Inscripcion.objects.filter(curso__instructor__usuario=request.user)
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        inscripciones = inscripciones.filter(estudiante__nombre_completo__icontains=busqueda)
    return render(request, 'inventario/lista_estudiantes.html', {'inscripciones': inscripciones})

@login_required
@role_required(allowed_roles=['Instructor'])
def evaluar_alumnos(request):
    inscripciones = Inscripcion.objects.filter(curso__instructor__usuario=request.user)
    cursos_instructor = Curso.objects.filter(instructor__usuario=request.user)
    curso_id = request.GET.get('curso')
    busqueda = request.GET.get('q', '').strip()
    
    if curso_id:
        inscripciones = inscripciones.filter(curso_id=curso_id)
    if busqueda:
        inscripciones = inscripciones.filter(estudiante__nombre_completo__icontains=busqueda)
    return render(request, 'inventario/evaluar_instructor.html', {
        'inscripciones': inscripciones, 'cursos': cursos_instructor
    })

@login_required
@role_required(allowed_roles=['Instructor'])
def registrar_nota(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    if request.method == 'POST':
        try:
            calificacion = float(request.POST.get('calificacion', 0))
            comentarios = request.POST.get('comentarios', '')
            Evaluacion.objects.create(inscripcion=inscripcion, calificacion=calificacion, comentarios=comentarios)
            messages.success(request, 'Nota registrada correctamente.')
        except (ValueError, TypeError):
            messages.error(request, 'Error al registrar la nota.')
        return redirect('inventario:evaluar_alumnos') 
    return render(request, 'inventario/registrar_nota.html', {'inscripcion': inscripcion})

# --- GESTIÓN ESTUDIANTES ---
@login_required
@role_required(allowed_roles=['Admin', 'Instructor'])
def gestion_estudiantes(request):
    busqueda = request.GET.get('busqueda', '').strip().lower()
    filtro_estado = request.GET.get('estado', '').strip()
    
    estudiantes = []
    
    with connection.cursor() as cursor:
        cursor.execute("EXEC SP_Listar_Estudiantes")
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            cleaned_row = []
            for val in row:
                if isinstance(val, bytes):
                    val = str(val)
                cleaned_row.append(val)
            
            estudiante_dict = dict(zip(columns, cleaned_row))
            if not estudiante_dict.get('estado'):
                estudiante_dict['estado'] = 'Activo'
            estudiantes.append(estudiante_dict)

    if busqueda:
        estudiantes = [
            e for e in estudiantes 
            if busqueda in str(e.get('nombre_completo', '')).lower() 
            or busqueda in str(e.get('email', '')).lower()
            or busqueda in str(e.get('usuario', '')).lower()
        ]

    if filtro_estado:
        estudiantes = [
            e for e in estudiantes 
            if str(e.get('estado', '')).lower() == filtro_estado.lower()
        ]

    usuarios = User.objects.filter(groups__name='Estudiante')

    return render(request, 'inventario/estudiantes.html', {
        'estudiantes': estudiantes, 
        'usuarios': usuarios
    })

@login_required
@role_required(allowed_roles=['Admin'])
def crear_estudiantes(request):
    if request.method == 'POST':
        username = request.POST.get('usuario')
        password = request.POST.get('contrasena')
        nombre = request.POST.get('nombre_completo')
        email = request.POST.get('email')
        estado_val = request.POST.get('estado', 'Activo')
        num_doc = request.POST.get('numero_documento', '').strip()

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.save()

                contra_cifrada = password.encode('utf-8') if password else b''

                if num_doc:
                    doc_resultado = cifrar_dato(num_doc) if 'cifrar_dato' in globals() else num_doc
                    doc_cifrado = doc_resultado.encode('utf-8') if isinstance(doc_resultado, str) else doc_resultado
                else:
                    doc_cifrado = b''

                Estudiante.objects.create(
                    usuario_auth=user,
                    usuario=username,
                    contrasena=contra_cifrada,
                    nombre_completo=nombre,
                    email=email,
                    telefono=request.POST.get('telefono'),
                    direccion=request.POST.get('direccion'),
                    tipo_documento=request.POST.get('tipo_documento'),
                    numero_documento=doc_cifrado,
                    estado=estado_val
                )
                messages.success(request, 'Estudiante registrado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al registrar: {e}')
    return redirect('inventario:gestion_estudiantes')

# Alias para compatibilidad por si tus urls llaman a registrar_estudiante
registrar_estudiante = crear_estudiantes
@login_required
def editar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    
    if request.method == 'POST':
        form = EstudianteForm(request.POST, instance=estudiante)
        
        if form.is_valid():
            # Como la contraseña ya está excluida en el formulario, 
            # form.save() actualizará los datos de manera limpia.
            estudiante_actualizado = form.save()
            
            # Sincronizamos los datos básicos en el modelo User de Django asociado (si aplica)
            if hasattr(estudiante_actualizado, 'usuario_auth') and estudiante_actualizado.usuario_auth:
                user = estudiante_actualizado.usuario_auth
                partes = estudiante_actualizado.nombre_completo.strip().split(' ', 1)
                user.first_name = partes[0]
                user.last_name = partes[1] if len(partes) > 1 else ''
                user.email = estudiante_actualizado.email
                user.save()

            messages.success(request, 'Estudiante actualizado correctamente.')
            return redirect('inventario:gestion_estudiantes')
    else:
        form = EstudianteForm(instance=estudiante)
        
    return render(request, 'inventario/editar_estudiante.html', {
        'form': form,
        'estudiante': estudiante
    })

@login_required
@role_required(allowed_roles=['Admin'])
def eliminar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    
    if request.method == 'POST':
        # Opcional pero recomendado: Si quieres borrar también el usuario de auth_user asociado
        usuario_auth = estudiante.usuario_auth
        
        estudiante.delete()
        
        # Eliminamos el usuario de auth_user para que no quede huérfano en la tabla de sistema
        if usuario_auth:
            usuario_auth.delete()
            
        messages.success(request, 'Estudiante eliminado correctamente.')
        return redirect('inventario:gestion_estudiantes')
        
    return render(request, 'inventario/confirmar_eliminacion.html', {'objeto': estudiante, 'tipo': 'estudiante'})
# --- GESTIÓN CURSOS ---
@login_required
def gestion_cursos(request):
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso creado exitosamente.')
            return redirect('inventario:gestion_cursos')
        else:
            messages.error(request, 'Error al crear el curso. Revisa los datos.')
    else:
        form = CursoForm()

    base_queryset = Curso.objects.all() if request.user.is_superuser else Curso.objects.filter(instructor__usuario=request.user)
    
    context = {
        'cursos': base_queryset,
        'form': form,
        'total_cursos': base_queryset.count(),
        'total_activos': base_queryset.filter(estado='Activo').count(),
        'costo_total': base_queryset.aggregate(Sum('costo'))['costo__sum'] or 0
    }
    
    return render(request, 'inventario/cursos.html', context)

@login_required
@role_required(allowed_roles=['Admin'])
def editar_curso(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado.')
            return redirect('inventario:gestion_cursos')
    else:
        form = CursoForm(instance=curso)
    return render(request, 'inventario/editar_curso.html', {'form': form, 'curso': curso})

# --- GESTIÓN PAGOS E INSTRUCTORES ---
@login_required
@role_required(allowed_roles=['Admin'])
def gestion_pagos(request):
    pagos = Pago.objects.all()
    return render(request, 'inventario/pagos.html', {'pagos': pagos})

@login_required
@role_required(allowed_roles=['Admin'])
def gestion_instructores(request):
    instructores = Instructor.objects.all()
    return render(request, 'inventario/instructores.html', {'instructores': instructores})

# --- INSCRIPCIONES ---
@login_required
@role_required(allowed_roles=['Admin', 'Estudiante'])
def gestion_inscripciones(request):
    inscripciones = Inscripcion.objects.all()
    estudiantes = Estudiante.objects.all()
    cursos = Curso.objects.all()
    instructores = Instructor.objects.all()
    
    return render(request, 'inventario/inscripciones.html', {
        'inscripciones': inscripciones,
        'estudiantes': estudiantes,
        'cursos': cursos,
        'instructores': instructores,
    })

@login_required
@role_required(allowed_roles=['Admin'])
def editar_inscripcion(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    if request.method == 'POST':
        form = InscripcionForm(request.POST, instance=inscripcion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscripción actualizada correctamente.')
            return redirect('inventario:gestion_inscripciones')
    else:
        form = InscripcionForm(instance=inscripcion)
    return render(request, 'inventario/editar_inscripcion.html', {'form': form, 'inscripcion': inscripcion})

# --- EVALUACIONES Y OTROS ---
@login_required
def gestion_evaluaciones(request):
    evaluaciones = []
    with connection.cursor() as cursor:
        cursor.execute("EXEC SP_Listar_Evaluaciones")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            cleaned_row = []
            for val in row:
                if isinstance(val, bytes):
                    try:
                        val = val.decode('utf-8', errors='ignore')
                    except Exception:
                        val = str(val)
                cleaned_row.append(val)
            evaluaciones.append(dict(zip(columns, cleaned_row)))

    return render(request, 'inventario/evaluaciones.html', {
        'evaluaciones': evaluaciones
    })

def custom_logout_view(request):
    logout(request)
    return redirect('core:index')

# --- FUNCIONES ADICIONALES ---

@login_required
@role_required(allowed_roles=['Admin'])
def crear_instructor(request):
    if request.method == 'POST':
        username = request.POST.get('usuario')
        password = request.POST.get('contrasena')
        nombre = request.POST.get('nombre')

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username)
                user.set_password(password)
                user.save()

                Instructor.objects.create(
                    usuario_auth=user,
                    nombre_completo=nombre,
                    especialidad=request.POST.get('especialidad'),
                    cedula_profesional=request.POST.get('cedula', '').encode(),
                    usuario=username,
                    contrasena=password.encode(),
                    estado=request.POST.get('estado')
                )
                messages.success(request, 'Instructor registrado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al registrar: {e}')
    return redirect('inventario:gestion_instructores')

# Alias para compatibilidad por si tus urls llaman a registrar_instructor
registrar_instructor = crear_instructor

@login_required
@role_required(allowed_roles=['Admin'])
def crear_curso(request):
    if request.method == 'POST':
        Curso.objects.create(
            nombre_curso=request.POST.get('nombre'),
            categoria=request.POST.get('categoria'),
            duracion_horas=request.POST.get('duracion'),
            costo=request.POST.get('costo'),
            estado=request.POST.get('estado'),
            cupo=request.POST.get('cupo'),
            instructor_id=request.POST.get('instructor')
        )
        messages.success(request, 'Curso registrado.')
    return redirect('inventario:gestion_cursos')

@login_required
@role_required(allowed_roles=['Admin'])
def eliminar_inscripcion(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    if request.method == 'POST':
        inscripcion.delete()
        messages.success(request, 'Inscripción eliminada.')
    return redirect('inventario:gestion_inscripciones')

@login_required
@role_required(allowed_roles=['Admin'])
def crear_inscripciones(request):
    if request.method == 'POST':
        form = InscripcionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscripción creada.')
    return redirect('inventario:gestion_inscripciones')

@login_required
@role_required(allowed_roles=['Admin'])
def editar_instructor(request, instructor_id):
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    if request.method == 'POST':
        form = InstructorForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Instructor actualizado.')
            return redirect('inventario:gestion_instructores')
    else:
        form = InstructorForm(instance=instructor)
    return render(request, 'inventario/editar_instructor.html', {'form': form, 'instructor': instructor})

@login_required
@role_required(allowed_roles=['Admin'])
def eliminar_instructor(request, instructor_id):
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    if request.method == 'POST':
        instructor.delete()
        messages.success(request, 'Instructor eliminado.')
        return redirect('inventario:gestion_instructores')
    return render(request, 'inventario/confirmar_eliminacion.html', {'objeto': instructor, 'tipo': 'instructor'})

@login_required
@role_required(allowed_roles=['Admin'])
def eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso eliminado.')
        return redirect('inventario:gestion_cursos')
    return render(request, 'inventario/confirmar_eliminacion.html', {'objeto': curso, 'tipo': 'curso'})

@login_required
@role_required(allowed_roles=['Admin'])
def reportes_view(request):
    return render(request, 'inventario/reportes.html')

@login_required
@role_required(allowed_roles=['Admin'])
def gestion_usuarios(request):
    usuarios = User.objects.select_related('perfil').all() 
    return render(request, 'admin_sistema/usuarios.html', {'usuarios': usuarios})

def crear_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente')
            return redirect('inventario:gestion_usuarios')
    else:
        form = UserCreationForm()
    return render(request, 'inventario/usuario_form.html', {'form': form})

def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    if request.method == 'POST':
        return redirect('inventario:gestion_usuarios')
    return render(request, 'inventario/usuario_form.html', {'form': None, 'usuario': usuario})

def eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente')
        return redirect('inventario:gestion_usuarios')
    return render(request, 'inventario/confirmar_eliminar.html', {'usuario': usuario})