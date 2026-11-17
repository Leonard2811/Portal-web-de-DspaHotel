from django.apps import AppConfig


class StaffConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'staff'
    verbose_name = 'Personal del Hotel'

    def ready(self):
        import staff.signals  # noqa: F401
