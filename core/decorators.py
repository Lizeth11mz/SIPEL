from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 1. Si no está autenticado, denegar acceso inmediatamente
            if not request.user.is_authenticated:
                raise PermissionDenied

            # 2. Permitir acceso total si es superusuario
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 3. Verificar si el usuario pertenece a alguno de los grupos permitidos
            user_groups = request.user.groups.values_list('name', flat=True)
            if any(rol in user_groups for rol in allowed_roles):
                return view_func(request, *args, **kwargs)
            
            # 4. Si no cumple ninguna condición, denegar acceso
            raise PermissionDenied
            
        return wrapper
    return decorator