from django.apps import AppConfig


class UserflowsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "userflows"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals

        # # We can also explicitly connect a signal handler....
        # request_finished.connect(signals.my_callback)
