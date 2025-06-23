from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users'

    # def ready(self):
    #     """
    #     Ilova tayyor bo'lganda signallarni import qilish.
    #     """
    #     import apps.users.signals # <-- SHU QATORNI QO'SHING
    
