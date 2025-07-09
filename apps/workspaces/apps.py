from django.apps import AppConfig


class WorkspacesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workspaces'

    def ready(self):
        """
        Ilova tayyor bo'lganda signallarni import qilish.
        """
        import apps.workspaces.signals
