import django
from django.core.management.base import BaseCommand

from lib.scrape_hcd_lib import run_scrape_hcd


class Command(BaseCommand):
    help = "Scrape HCD housing element compliance data and save it to Airtable. Intended to run nightly."

    def add_arguments(self, parser: django.core.management.base.CommandParser) -> None:
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Get all the data but print it to the console instead of updating Airtable.",
        )
        parser.add_argument(
            "--try_exception",
            action="store_true",
            help="Instead of doing something useful, raise an exception to make sure we get alerted.",
        )
        super().add_arguments(parser)

    def handle(self, dry_run, try_exception, *args, **kwargs) -> None:
        if try_exception:
            raise Exception("This is a test exception in scrape_hcd.py")
        run_scrape_hcd(dry_run)
