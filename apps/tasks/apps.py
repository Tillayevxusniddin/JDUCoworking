# apps/tasks/apps.py

from django.apps import AppConfig
import sys  # <-- Sistemani import qilamiz

class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tasks'

    def ready(self):
        """
        Ilova ishga tushganda rejalashtirilgan vazifalarni ishga tushirish.
        Scheduler faqat `runserver` buyrug'i bilan ishga tushiriladi.
        """
        # --- XATOLIKNI TUZATISH UCHUN QO'SHILGAN SHART ---
        if 'runserver' in sys.argv:
            from . import scheduler
            scheduler.start()
        # ----------------------------------------------------