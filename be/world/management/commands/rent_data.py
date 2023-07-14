import logging

from django.db.models import Count
from lib.mgmt_lib import Home3Command

from world.models import RentalData

log = logging.getLogger(__name__)


class Command(Home3Command):
    help = "Commands to manage rent data in our system"

    # Positional arguments
    def add_arguments(self, parser):
        parser.add_argument("cmd_name", type=str, help="Command to run. Valid option are: dedup, reset_credits")

    def handle(self, *args, **options):
        log.setLevel(logging.INFO)
        if options["cmd_name"] == "reset_credits":
            log.info("Removing out of credit errors from our Rentometer data cache")
            no_credits = RentalData.objects.filter(details__status_code=402)  # 402 means no credits available
            no_credits.delete()
        elif options["cmd_name"] == "dedup":
            rd_dupes = (
                RentalData.objects.values("parcel_id", "br", "ba").annotate(cnt=Count("parcel_id")).filter(cnt__gt=1)
            )
            log.info(f"Found {len(rd_dupes)} duplicates. Removing:")
            for rd in rd_dupes:
                items = RentalData.objects.filter(parcel_id=rd["parcel_id"], br=rd["br"], ba=rd["ba"])
                assert len(items) > 1
                for item in items[1:]:
                    item.delete()
            log.info("Removed duplicates.")

        else:
            log.error(f"Unknown command {options['cmd_name']}")
