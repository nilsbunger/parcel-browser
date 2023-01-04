import django
from django.apps import apps

# Create a django management command that can take a list of APNs, and then run
# the dumpdata command on each of them. This will allow us to create a fixture.


"""
Additional treatment for the dumpdata command.
Location example: project/app/management/commands/loaddata.py
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import dumpdata


class Command(dumpdata.Command):
    def add_arguments(self, parser: django.core.management.base.CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--apns",
            dest="apns",
            help="Only dump objects with given APNs. Works on any model with an APN column. "
            "Accepts a comma-separated list of keys.",
        )

    def handle(self, *app_labels: str, **options) -> None:

        # Create --apns argument on dumpdata, to allow us to select data by APN
        apns: str = options["apns"]
        if apns and len(app_labels) != 1:
            raise CommandError("You can only use --apns option with one model")
        if apns:
            # Translate APNs into primary keys
            apns_list = [apn.strip() for apn in apns.split(",")]
            app_label, model_label = app_labels[0].split(".")
            app_config = apps.get_app_config(app_label)
            model = app_config.get_model(model_label)
            pks = [str(x) for x in model.objects.filter(apn__in=apns_list).values_list("pk", flat=True)]
            options["primary_keys"] = ",".join(pks)
        super().handle(*app_labels, **options)
