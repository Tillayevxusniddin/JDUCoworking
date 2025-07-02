from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.jobs'
    verbose_name = 'Ishlar va Arizalar'

    def ready(self):
        import apps.jobs.signals # Signallarni import qilish
