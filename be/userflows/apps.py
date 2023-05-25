from django.apps import AppConfig


class UserflowsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "userflows"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        pass

        # # We can also explicitly connect a signal handler....
        # request_finished.connect(signals.my_callback)
