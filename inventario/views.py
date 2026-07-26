# inventario/views.py
print("--- LEYENDO EL ARCHIVO VIEWS.PY CORRECTO ---")
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User,Group
from django.db import connection
from django.db.models import Q
from django.db import transaction 
from core.decorators import role_required 
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Sum
from django.contrib.auth import update_session_auth_hash
from .utils import cifrar_dato
from .models import Estudiante, Curso, Inscripcion, Pago, Instructor, Evaluacion
from .forms import EstudianteForm, CursoForm, InstructorForm, InscripcionForm,CambiarContrasenaAdminForm

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
            for i, val in enumerate(row):
                col_name = columns[i]
                if isinstance(val, bytes):
                    # Decodificar correctamente si es direccion o texto binario
                    try:
                        val = val.decode('utf-8')
                    except UnicodeDecodeError:
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
            or busqueda in str(e.get('direccion', '')).lower() # Opcional: permitir buscar por dirección también
        ]

    if filtro_estado:
        estudiantes = [
            e for e in estudiantes 
            if str(e.get('estado', '')).lower() == filtro_estado.lower()
        ]

    usuarios = User.objects.filter(groups__name='Estudiante')

    # Cálculo correcto de estadísticas para las tarjetas de la vista
    total_estudiantes = len(estudiantes)
    total_activos = sum(1 for e in estudiantes if str(e.get('estado', '')).capitalize() == 'Activo')
    total_inactivos = sum(1 for e in estudiantes if str(e.get('estado', '')).capitalize() == 'Inactivo')

    return render(request, 'inventario/estudiantes.html', {
        'estudiantes': estudiantes, 
        'usuarios': usuarios,
        'total_estudiantes': total_estudiantes,
        'total_activos': total_activos,
        'total_inactivos': total_inactivos,
    })

@login_required
@role_required(allowed_roles=['Admin'])
def crear_estudiantes(request):
    if request.method == 'POST':
        username = request.POST.get('usuario')
        password = request.POST.get('contrasena')
        nombre = request.POST.get('nombre_completo', '').strip().upper()
        email = request.POST.get('email')
        estado_val = request.POST.get('estado', 'Activo')
        num_doc = request.POST.get('numero_documento', '').strip()
        tipo_doc = request.POST.get('tipo_documento', '').upper()
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion', '').upper()

        try:
            with transaction.atomic():
                # Dividir el nombre completo en partes para guardarlo en el modelo User de Django
                partes_nombre = nombre.split(' ', 1)
                primer_nombre = partes_nombre[0]
                apellido = partes_nombre[1] if len(partes_nombre) > 1 else ''

                # 1. Crear el usuario de autenticación de Django incluyendo el nombre
                user = User.objects.create_user(
                    username=username, 
                    email=email, 
                    first_name=primer_nombre, 
                    last_name=apellido
                )
                user.set_password(password)
                user.save()

                # 2. Asignar automáticamente el grupo "Estudiante" para que no aparezca "Sin rol"
                try:
                    grupo_estudiante = Group.objects.get(name='Estudiante')
                    user.groups.add(grupo_estudiante)
                except Group.DoesNotExist:
                    grupo_estudiante = Group.objects.create(name='Estudiante')
                    user.groups.add(grupo_estudiante)

                contra_cifrada = password.encode('utf-8') if password else b''

                # 3. Insertar directamente con SQL crudo utilizando EncryptByKey y usuario_id
                with connection.cursor() as cursor:
                    cursor.execute("""
                        OPEN SYMMETRIC KEY ClaveDatos DECRYPTION BY CERTIFICATE CertificadoDatos;
                        
                        INSERT INTO Estudiantes (
                            usuario_id, usuario, contrasena, nombre_completo, 
                            email, telefono, direccion, tipo_documento, numero_documento, estado
                        ) 
                        VALUES (
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, EncryptByKey(Key_GUID('ClaveDatos'), CONVERT(VARBINARY(MAX), %s)), %s
                        );
                        
                        CLOSE SYMMETRIC KEY ClaveDatos;
                    """, [
                        user.id,        # Corresponde a usuario_id
                        username, 
                        contra_cifrada, 
                        nombre, 
                        email, 
                        telefono, 
                        direccion, 
                        tipo_doc, 
                        num_doc,  
                        estado_val
                    ])

                messages.success(request, 'Estudiante registrado correctamente.')
                
        except Exception as e:
            print("==================================================")
            print("--- ERROR CRÍTICO AL CREAR ESTUDIANTE:", str(e))
            print("==================================================")
            messages.error(request, f'Error al registrar: {e}')
            
    return redirect('inventario:gestion_estudiantes')

registrar_estudiante = crear_estudiantes
@login_required
def editar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    
    if request.method == 'POST':
        form = EstudianteForm(request.POST, instance=estudiante)
        
        # En lugar de usar form.is_valid() estricto que bloquea campos cifrados/readonly,
        # validamos los campos básicos directamente o procesamos la data del POST de forma segura.
        try:
            with transaction.atomic():
                # 1. Extraemos los valores directamente del diccionario request.POST
                nombre = request.POST.get('nombre_completo', '').strip()
                email = request.POST.get('email', '').strip()
                telefono = request.POST.get('telefono', '').strip()
                tipo_doc = request.POST.get('tipo_documento', '').strip()
                estado = request.POST.get('estado', 'Activo').strip()
                direccion = request.POST.get('direccion', '').strip()
                usuario = request.POST.get('usuario', '').strip()
                nuevo_num_doc = request.POST.get('numero_documento', '').strip()
                
                with connection.cursor() as cursor:
                    # 2. Si el usuario ingresó un nuevo número de documento, lo ciframos con SQL Server
                    if nuevo_num_doc:
                        cursor.execute("""
                            OPEN SYMMETRIC KEY ClaveDatos DECRYPTION BY CERTIFICATE CertificadoDatos;
                            
                            UPDATE Estudiantes 
                            SET nombre_completo = %s,
                                email = %s,
                                telefono = %s,
                                direccion = %s,
                                usuario = %s,
                                tipo_documento = %s,
                                estado = %s,
                                numero_documento = EncryptByKey(Key_GUID('ClaveDatos'), CONVERT(VARBINARY(MAX), %s))
                            WHERE estudiante_id = %s;
                            
                            CLOSE SYMMETRIC KEY ClaveDatos;
                        """, [nombre, email, telefono, direccion, usuario, tipo_doc, estado, nuevo_num_doc, estudiante_id])
                    
                    # 3. Si dejó el documento en blanco, actualizamos el resto de campos sin tocar el documento actual
                    else:
                        cursor.execute("""
                            UPDATE Estudiantes 
                            SET nombre_completo = %s,
                                email = %s,
                                telefono = %s,
                                direccion = %s,
                                usuario = %s,
                                tipo_documento = %s,
                                estado = %s
                            WHERE estudiante_id = %s;
                        """, [nombre, email, telefono, direccion, usuario, tipo_doc, estado, estudiante_id])

                # 4. Sincronizamos con el usuario de autenticación si existe
                if hasattr(estudiante, 'usuario_auth') and estudiante.usuario_auth:
                    user = estudiante.usuario_auth
                    partes = nombre.strip().split(' ', 1)
                    user.first_name = partes[0]
                    user.last_name = partes[1] if len(partes) > 1 else ''
                    user.email = email
                    user.save()

            messages.success(request, 'Estudiante actualizado correctamente.')
            return redirect('inventario:gestion_estudiantes')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar en la base de datos: {e}')
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
        usuario_auth = estudiante.usuario_auth
        estudiante.delete()
        
        if usuario_auth:
            usuario_auth.delete()
            
        messages.success(request, 'Estudiante eliminado correctamente.')
        return redirect('inventario:gestion_estudiantes')
        
    return render(request, 'inventario/confirmar_eliminacion.html', {'objeto': estudiante, 'tipo': 'estudiante'})

# --- GESTIÓN CURSOS ---
@login_required
def gestion_cursos(request):
    # Definimos la consulta de instructores fuera para tenerla disponible siempre
    instructores = Instructor.objects.all()

    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    nuevo_curso = form.save(commit=False)
                    nuevo_curso.cupo_disponible = nuevo_curso.cupo_maximo
                    nuevo_curso.save()
                messages.success(request, 'Curso creado exitosamente.')
                return redirect('inventario:gestion_cursos')
            except Exception as e:
                messages.error(request, f'Error al registrar el curso: {e}')
        else:
            messages.error(request, 'Error al crear el curso. Revisa los datos.')
    else:
        form = CursoForm()

    # CORREGIDO AQUÍ: Usamos usuario_auth para que el filtro encuentre los cursos asignados al instructor logueado
    base_queryset = Curso.objects.all() if request.user.is_superuser else Curso.objects.filter(instructor__usuario_auth=request.user)
    
    # Capturamos los parámetros de búsqueda y filtro de la URL (GET)
    query = request.GET.get('q', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    # Aplicamos los filtros sobre una copia del queryset para la tabla
    cursos_filtrados = base_queryset
    if query:
        cursos_filtrados = cursos_filtrados.filter(nombre_curso__icontains=query)
    
    if estado_filtro:
        cursos_filtrados = cursos_filtrados.filter(estado=estado_filtro)

    context = {
        'cursos': cursos_filtrados,
        'form': form,
        'instructores': instructores,
        'total_cursos': base_queryset.count(),
        'total_activos': base_queryset.filter(estado='Activo').count(),
        'costo_activos': base_queryset.filter(estado='Activo').aggregate(Sum('costo'))['costo__sum'] or 0,
        'costo_total': base_queryset.aggregate(Sum('costo'))['costo__sum'] or 0
    }
    
    return render(request, 'inventario/cursos.html', context)
@login_required
@role_required(allowed_roles=['Admin'])
def crear_curso(request):
    if request.method == 'POST':
        try:
            Curso.objects.create(
                nombre_curso=request.POST.get('nombre_curso'),
                categoria=request.POST.get('categoria'),
                duracion_horas=request.POST.get('duracion_horas'),
                costo=request.POST.get('costo'),
                estado=request.POST.get('estado'),
                cupo_maximo=request.POST.get('cupo_maximo'),
                instructor_id=request.POST.get('instructor')
            )
            messages.success(request, 'Curso registrado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al registrar el curso: {e}')
            
    return redirect('inventario:gestion_cursos')

@login_required
@role_required(allowed_roles=['Admin'])
def editar_curso(request, curso_id):
    # Buscamos el curso existente
    curso = get_object_or_404(Curso, pk=curso_id)
    
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado.')
            return redirect('inventario:gestion_cursos')
        else:
            # ESTO TE PERMITIRÁ VER EL ERROR EXACTO EN LA TERMINAL DE DJANGO
            print("Errores en el formulario de curso:", form.errors)
            messages.error(
                request, 'Por favor, corrige los errores en el formulario.'
            )
    else:
        form = CursoForm(instance=curso)
    return render(request, 'inventario/editar_curso.html', {'form': form, 'curso': curso})


@login_required
@role_required(allowed_roles=['Admin'])
def eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso eliminado.')
        return redirect('inventario:gestion_cursos')
    return render(request, 'inventario/confirmar_eliminacion.html', {'objeto': curso, 'tipo': 'curso'})

# --- GESTIÓN PAGOS ---
@login_required
@role_required(allowed_roles=['Admin'])
def gestion_pagos(request):
    pagos = Pago.objects.all()
    return render(request, 'inventario/pagos.html', {'pagos': pagos})


#instructores-------------------------
@login_required
@role_required(allowed_roles=['Admin'])
def gestion_instructores(request):
    query = request.GET.get('q', '')
    especialidad_filtro = request.GET.get('especialidad', '')
    estado_filtro = request.GET.get('estado', '')

    instructores = Instructor.objects.all()

    if query:
        instructores = instructores.filter(
            Q(nombre_completo__icontains=query) | 
            Q(email__icontains=query) | 
            Q(especialidad__icontains=query)
        )
    
    if especialidad_filtro:
        instructores = instructores.filter(especialidad=especialidad_filtro)
        
    if estado_filtro:
        instructores = instructores.filter(estado=estado_filtro)

    total_instructores = Instructor.objects.count()
    total_activos = Instructor.objects.filter(estado='Activo').count()
    total_inactivos = Instructor.objects.filter(estado='Inactivo').count()

    lista_especialidades = Instructor.objects.values_list('especialidad', flat=True).distinct()

    context = {
        'instructores': instructores,
        'total_instructores': total_instructores,
        'total_activos': total_activos,
        'total_inactivos': total_inactivos,
        'lista_especialidades': lista_especialidades,
    }
    
    return render(request, 'inventario/instructores.html', context)
@login_required
@role_required(allowed_roles=['Admin'])
def crear_instructor(request):
    if request.method == 'POST':
        username = request.POST.get('usuario')
        password = request.POST.get('contrasena')
        nombre = request.POST.get('nombre_completo', '').strip().upper()
        email = request.POST.get('email')
        estado_val = request.POST.get('estado', 'Activo')
        cedula_raw = request.POST.get('cedula_profesional', '').strip()
        especialidad = request.POST.get('especialidad', '').upper().strip()
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion', '').upper().strip()

        try:
            with transaction.atomic():
                # Dividir el nombre completo en partes para guardarlo en el modelo User de Django
                partes_nombre = nombre.split(' ', 1)
                primer_nombre = partes_nombre[0]
                apellido = partes_nombre[1] if len(partes_nombre) > 1 else ''

                # 1. Crear el usuario de autenticación de Django incluyendo el nombre
                user = User.objects.create_user(
                    username=username, 
                    email=email, 
                    first_name=primer_nombre, 
                    last_name=apellido
                )
                user.set_password(password)
                user.save()

                # 2. Asignar automáticamente el grupo "Instructor" para que no aparezca "Sin rol"
                try:
                    grupo_instructor = Group.objects.get(name='Instructor')
                    user.groups.add(grupo_instructor)
                except Group.DoesNotExist:
                    grupo_instructor = Group.objects.create(name='Instructor')
                    user.groups.add(grupo_instructor)

                contra_cifrada = password.encode('utf-8') if password else b''

                # 3. Insertar directamente con SQL crudo utilizando EncryptByKey y usuario_id
                with connection.cursor() as cursor:
                    cursor.execute("""
                        OPEN SYMMETRIC KEY ClaveDatos DECRYPTION BY CERTIFICATE CertificadoDatos;
                        
                        INSERT INTO Instructores (
                            usuario_id, usuario, contrasena, nombre_completo, 
                            email, telefono, direccion, especialidad, cedula_profesional, estado
                        ) 
                        VALUES (
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, EncryptByKey(Key_GUID('ClaveDatos'), CONVERT(VARBINARY(MAX), %s)), %s
                        );
                        
                        CLOSE SYMMETRIC KEY ClaveDatos;
                    """, [
                        user.id,        # Corresponde a usuario_id
                        username, 
                        contra_cifrada, 
                        nombre, 
                        email, 
                        telefono, 
                        direccion, 
                        especialidad, 
                        cedula_raw,  
                        estado_val
                    ])

                messages.success(request, 'Instructor registrado correctamente.')
                
        except Exception as e:
            print("==================================================")
            print("--- ERROR CRÍTICO AL CREAR INSTRUCTOR:", str(e))
            print("==================================================")
            messages.error(request, f'Error al registrar: {e}')
            
    return redirect('inventario:gestion_instructores')

registrar_instructor = crear_instructor


@login_required
@role_required(allowed_roles=['Admin'])
def editar_instructor(request, instructor_id):
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    
    if request.method == 'POST':
        form = InstructorForm(request.POST, instance=instructor)
        
        try:
            with transaction.atomic():
                # 1. Extraemos los valores directamente del diccionario request.POST
                nombre = request.POST.get('nombre_completo', '').strip().upper()
                email = request.POST.get('email', '').strip()
                telefono = request.POST.get('telefono', '').strip()
                especialidad = request.POST.get('especialidad', '').upper().strip()
                estado = request.POST.get('estado', 'Activo').strip()
                direccion = request.POST.get('direccion', '').upper().strip()
                usuario = request.POST.get('usuario', '').strip()
                nueva_cedula = request.POST.get('cedula_profesional', '').strip()
                
                with connection.cursor() as cursor:
                    # 2. Si el usuario ingresó una nueva cédula, la ciframos con SQL Server
                    if nueva_cedula:
                        cursor.execute("""
                            OPEN SYMMETRIC KEY ClaveDatos DECRYPTION BY CERTIFICATE CertificadoDatos;
                            
                            UPDATE Instructores 
                            SET nombre_completo = %s,
                                email = %s,
                                telefono = %s,
                                direccion = %s,
                                usuario = %s,
                                especialidad = %s,
                                estado = %s,
                                cedula_profesional = EncryptByKey(Key_GUID('ClaveDatos'), CONVERT(VARBINARY(MAX), %s))
                            WHERE instructor_id = %s;
                            
                            CLOSE SYMMETRIC KEY ClaveDatos;
                        """, [nombre, email, telefono, direccion, usuario, especialidad, estado, nueva_cedula, instructor_id])
                    
                    # 3. Si dejó la cédula en blanco, actualizamos el resto de campos sin tocar la cédula actual
                    else:
                        cursor.execute("""
                            UPDATE Instructores 
                            SET nombre_completo = %s,
                                email = %s,
                                telefono = %s,
                                direccion = %s,
                                usuario = %s,
                                especialidad = %s,
                                estado = %s
                            WHERE instructor_id = %s;
                        """, [nombre, email, telefono, direccion, usuario, especialidad, estado, instructor_id])

                # 4. Sincronizamos con el usuario de autenticación si existe
                if hasattr(instructor, 'usuario_auth') and instructor.usuario_auth:
                    user = instructor.usuario_auth
                    partes = nombre.strip().split(' ', 1)
                    user.first_name = partes[0]
                    user.last_name = partes[1] if len(partes) > 1 else ''
                    user.email = email
                    user.save()

            messages.success(request, 'Instructor actualizado correctamente.')
            return redirect('inventario:gestion_instructores')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar en la base de datos: {e}')
    else:
        form = InstructorForm(instance=instructor)
        if 'cedula_profesional' in form.fields:
            form.fields['cedula_profesional'].initial = ''
        
    return render(request, 'inventario/editar_instructor.html', {
        'form': form,
        'instructor': instructor
    })
@login_required
@role_required(allowed_roles=['Admin'])
def eliminar_instructor(request, instructor_id):
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    if request.method == 'POST':
        instructor.delete()
        messages.success(request, 'Instructor eliminado.')
        return redirect('inventario:gestion_instructores')
    return render(request, 'inventario/confirmar_eliminacion.html', {'objeto': instructor, 'tipo': 'instructor'})


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


login_required
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

@login_required
@role_required(allowed_roles=['Admin'])
def eliminar_inscripcion(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id)
    if request.method == 'POST':
        inscripcion.delete()
        messages.success(request, 'Inscripción eliminada.')
    return redirect('inventario:gestion_inscripciones')


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



@login_required
@role_required(allowed_roles=['Admin'])
def reportes_view(request):
    return render(request, 'inventario/reportes.html')
#---------usuarios-----------------
@login_required
@role_required(allowed_roles=['Admin'])
def gestion_usuarios(request):
    usuarios = User.objects.all().order_by('id')
    
    # Capturar filtros de la URL
    query = request.GET.get('q')
    estado = request.GET.get('estado')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
        
    if estado == 'activo':
        usuarios = usuarios.filter(is_active=True)
    elif estado == 'inactivo':
        usuarios = usuarios.filter(is_active=False)
        
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

@login_required
def cambiar_contrasena_usuario(request, user_id):
    usuario_obj = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = CambiarContrasenaAdminForm(user=usuario_obj, data=request.POST)
        if form.is_valid():
            user = form.save()
            
            if request.user.pk == user.pk:
                update_session_auth_hash(request, user)
                
            messages.success(request, "¡Contraseña actualizada correctamente!")
            return redirect('inventario:gestion_usuarios') 
    else:
        form = CambiarContrasenaAdminForm(user=usuario_obj)
        
    context = {
        'form': form,
        'usuario': usuario_obj,
        'titulo': f"Cambiar Contraseña de {usuario_obj.username}"
    }
    
    return render(request, 'inventario/form.html', context)

def custom_logout_view(request):
    logout(request)
    return redirect('core:index')

    
# --- VISTAS POR ROL ---
@login_required
@role_required(allowed_roles=['Estudiante'])
def registros_estudiante(request):
    return render(request, 'inventario/registros_estudiante.html')

@login_required
@role_required(allowed_roles=['Instructor'])
def registros_instructor(request):
    instructor = Instructor.objects.filter(usuario_auth=request.user).first()
    
    context = {
        'nombre_real': instructor.nombre_completo if instructor else request.user.get_full_name() or request.user.username,
        'permiso': 'Instructor',
        'usuario': request.user.username,
    }
    return render(request, 'inventario/registros_instructor.html', context)
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
