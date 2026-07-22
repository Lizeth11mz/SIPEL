# C:\Users\ADMIN\Desktop\proyecto\sma_orler\core\apps.py

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # 📢 Importante: Este método asegura que Django cargue y registre las señales
        # definidas en core.signals al iniciar la aplicación.
        import core.signals