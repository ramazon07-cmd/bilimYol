from django.apps import AppConfig


class ProfilingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiling"

    def ready(self):
        from . import signals  # noqa: F401
