# utils.py
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet_instance():
    """Retorna una instancia de Fernet usando la clave de configuración."""
    return Fernet(settings.FERNET_KEY)

def cifrar_dato(dato_str):
    """Cifra una cadena de texto y devuelve un string legible (base64) en lugar de bytes."""
    if not dato_str or str(dato_str).strip() == "":
        return ""
    f = get_fernet_instance()
    # Si por error ya viene en bytes, lo decodificamos primero para cifrarlo bien
    if isinstance(dato_str, bytes):
        dato_str = dato_str.decode('utf-8', errors='ignore')
    # Cifra y decodifica a utf-8 para que devuelva una cadena de texto limpia (str)
    return f.encrypt(str(dato_str).encode('utf-8')).decode('utf-8')

def descifrar_dato(dato_binario):
    """Descifra un dato (ya sea binario, memoryview o string cifrado) a cadena de texto para mostrarlo."""
    if not dato_binario:
        return ""
    try:
        f = get_fernet_instance()
        
        # Si ya viene como string plano (o token cifrado en texto)
        if isinstance(dato_binario, str):
            # Intentamos descifrarlo por si es un token en texto plano
            try:
                return f.decrypt(dato_binario.encode('utf-8')).decode('utf-8')
            except Exception:
                # Si no se puede descifrar, significa que es texto plano normal
                return dato_binario
                
        # Si el driver de SQL Server o Django devuelve un memoryview, lo convertimos a bytes
        if isinstance(dato_binario, memoryview):
            dato_binario = bytes(dato_binario)
            
        # Si es un objeto bytes, lo desciframos
        if isinstance(dato_binario, bytes):
            return f.decrypt(dato_binario).decode('utf-8')
            
        return str(dato_binario)
    except Exception:
        return ""