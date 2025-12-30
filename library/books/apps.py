from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'books'

    def ready(self):
        # Import signals to connect handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
