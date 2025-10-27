from django.apps import AppConfig


class AcademyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "academy"

    def ready(self) -> None:
        from . import signals  # noqa: F401
