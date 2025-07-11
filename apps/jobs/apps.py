from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.jobs'
    verbose_name = 'Jobs Management'

    def ready(self):
        import apps.jobs.signals 
