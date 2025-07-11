# apps/tasks/apps.py

from django.apps import AppConfig
import sys 

class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tasks'

    def ready(self):
        """
        Import signals to ensure they are registered when the app is ready.
        """
        if 'runserver' in sys.argv:
            from . import scheduler
            scheduler.start()
        