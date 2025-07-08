# apps/meetings/apps.py

from django.apps import AppConfig

class MeetingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.meetings'

    def ready(self):
        import apps.meetings.signals