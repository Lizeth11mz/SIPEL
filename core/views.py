from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from core.models import PerfilUsuario
from inventario.forms import UsuarioForm

# ============================================================
# 1. VISTAS PÚBLICAS
# ============================================================

def index(request):
    if request.user.is_authenticated:
        return home_registros(request)
    return render(request, 'core/index.html')

def bienvenido(request): return render(request, 'core/bienvenidos.html')
def acerca_de(request): return render(request, 'core/acerca_de.html')
def servicios(request): return render(request, 'core/servicios.html')
def contacto(request): return render(request, 'core/contacto.html')

# ============================================================
# 2. LOGIN PERSONALIZADO
# ============================================================

def login_view(request):
    rol_solicitado = request.GET.get("role", None)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "core/login.html", {'role': rol_solicitado})

        # Obtener rol numérico
        if user.is_superuser:
            rol_num = 1 # Admin
        else:
            try:
                rol_num = user.perfil.nivel_acceso
            except PerfilUsuario.DoesNotExist:
                messages.error(request, "Tu cuenta no tiene un perfil configurado.")
                return render(request, "core/login.html", {'role': rol_solicitado})

        # Mapeo a texto para lógica interna
        mapa_roles = {1: "Admin", 2: "Instructor", 3: "Estudiante"}
        rol_usuario = mapa_roles.get(rol_num)

        # Validación de roles
        if not user.is_superuser and rol_solicitado and rol_usuario.lower() != rol_solicitado.lower():
            messages.error(request, f"Acceso restringido. Tu cuenta es {rol_usuario}.")
            return render(request, "core/login.html", {'role': rol_solicitado})

        login(request, user)
        
        # Redirección
        if rol_usuario == "Admin": return redirect("inventario:registros")
        if rol_usuario == "Estudiante": return redirect("inventario:registros_estudiante")
        return redirect("inventario:registros_instructor")

    return render(request, "core/login.html", {'role': rol_solicitado})


@login_required
def home_registros(request):
    try:
        if request.user.is_superuser: return redirect("inventario:registros")
        rol_num = request.user.perfil.nivel_acceso
        if rol_num == 1: return redirect("inventario:registros")
        if rol_num == 3: return redirect("inventario:registros_estudiante")
        return redirect("inventario:registros_instructor")
    except:
        return redirect('core:index')

def custom_logout_view(request):
    logout(request)
    return redirect("core:index")
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventario:gestion_usuarios')
    else:
        form = UsuarioForm()
    
    return render(request, 'inventario/usuario_form.html', {'form': form})
# En core/views.py

# En core/views.py
def editar_usuario_CORRECTO(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    form = UsuarioForm(instance=usuario)
    return render(request, 'inventario/usuario_form.html', {'form': form, 'usuario': usuario})
def eliminar_usuario(request, usuario_id): # Cambiado de pk a usuario_id
    usuario = get_object_or_404(User, pk=usuario_id)
    if request.method == 'POST':
        usuario.delete()
        return redirect('inventario:gestion_usuarios')
    return render(request, 'inventario/usuario_confirm_delete.html', {'usuario': usuario})