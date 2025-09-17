
from django.apps import AppConfig


class EngenhariaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'engenharia'

    def ready(self):
            # Importa o arquivo de signals para que o decorator @receiver seja executado
            import engenharia.signals
