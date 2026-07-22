from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied
from core.decorators import role_required

# =======================================================
# 🛡️ DECORADOR DE SEGURIDAD   

admin_required = role_required(['Administración'])
# =======================================================

def admin_required(view_func):
    """Verifica que el usuario esté logueado y tenga rol de Admin"""
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and \
           hasattr(request.user, 'perfilusuario') and \
           request.user.perfilusuario.rol.lower() in ['admin', 'administrador']:
            return view_func(request, *args, **kwargs)
        else:
            # Si no es admin, renderiza la misma vista pero mostrará el error en la plantilla
            # o puedes usar raise PermissionDenied para un error 403.
            usuarios_listado = User.objects.all().select_related('perfilusuario')
            return render(request, 'admin_sistema/usuarios.html', {"usuarios": usuarios_listado})
    return wrap

# =======================================================
# 🔵 VISTAS DE LOGIN
# =======================================================

def login_admin(request):
    return render(request, 'admin_sistema/login_admin.html', {})

def login_warehouse(request):
    return render(request, 'admin_sistema/login_warehouse.html', {})

def login_user(request):
    return render(request, 'admin_sistema/login_user.html', {})

# =======================================================
# 🟦 CRUD DE USUARIOS
# =======================================================

@login_required
@admin_required
def gestion_usuarios(request):
    if request.method == 'POST':
        username = request.POST.get('usuario')
        first_name = request.POST.get('nombre')
        last_name = request.POST.get('apellidos')
        email = request.POST.get('email')
        password = request.POST.get('contrasena')
        confirm_password = request.POST.get('confirmar_contrasena')
        rol_nombre = request.POST.get('rol') # Ejemplo: "Admin", "Instructor", "Estudiante"
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('inventario:gestion_usuarios')

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            
            # Asignar el grupo nativo correspondiente
            if rol_nombre:
                grupo, created = Group.objects.get_or_create(name=rol_nombre)
                user.groups.add(grupo)

            messages.success(request, f'Usuario "{username}" creado exitosamente.')
        except IntegrityError:
            messages.error(request, 'El nombre de usuario o email ya existen.')
        except Exception as e:
            messages.error(request, f'Error inesperado: {e}')
        
        return redirect('inventario:gestion_usuarios')
    
    # Manejo de filtros (Buscador y Estado) de forma limpia usando solo User nativo
    usuarios_listado = User.objects.all().prefetch_related('groups').order_by('username')
    q = request.GET.get('q')
    estado = request.GET.get('estado')
    
    if q:
        usuarios_listado = usuarios_listado.filter(username__icontains=q)
    if estado == 'activo':
        usuarios_listado = usuarios_listado.filter(is_active=True)
    elif estado == 'inactivo':
        usuarios_listado = usuarios_listado.filter(is_active=False)

    return render(request, 'admin_sistema/usuarios.html', {"usuarios": usuarios_listado})

@login_required
@admin_required
def crear_usuario(request):
    return render(request, 'admin_sistema/crear_usuario.html')

@login_required
@admin_required
def editar_usuario(request, pk):
    usuario = get_object_or_404(User.objects.prefetch_related('groups'), pk=pk)

    if request.method == 'POST':
        usuario.first_name = request.POST.get('nombre')
        usuario.last_name = request.POST.get('apellidos')
        usuario.email = request.POST.get('email')
        usuario.is_active = (request.POST.get('estado') == 'activo')
        
        password = request.POST.get('contrasena')
        if password:
            usuario.set_password(password)
        usuario.save()

        # Actualizar grupo de forma segura
        rol_nombre = request.POST.get('rol')
        if rol_nombre:
            usuario.groups.clear()
            grupo, created = Group.objects.get_or_create(name=rol_nombre)
            usuario.groups.add(grupo)

        messages.success(request, f'Usuario "{usuario.username}" actualizado.')
        return redirect('inventario:gestion_usuarios')

    return render(request, 'admin_sistema/editar_usuario.html', {'usuario': usuario})

@login_required
@admin_required
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.user.pk == usuario.pk:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
    else:
        usuario.delete()
        messages.success(request, f'Usuario eliminado.')
    return redirect('inventario:gestion_usuarios')

# =======================================================
# 📊 REPORTES
# =======================================================

@login_required
def generar_reportes(request):
    return render(request, 'admin_sistema/reportes.html', {})