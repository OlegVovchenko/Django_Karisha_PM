from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Салон красоты "Karisha PM"'

    def ready(self):
        import core.signals
