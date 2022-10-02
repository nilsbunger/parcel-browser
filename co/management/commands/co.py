from enum import Enum
import logging
import pprint
import sys

from django.core.management import BaseCommand

from lib import mgmt_cmd_lib


class CoCmd(Enum):
    eligible = 1


class Command(BaseCommand):
    help = "Parse MLS Listings for San Diego, analyze, and put into database. Optionally re-scrape"

    def add_arguments(self, parser):
        parser.add_argument("cmd", choices=CoCmd.__members__)
        parser.add_argument("rest", action="store", nargs="*")
        parser.add_argument(
            "--fetch", action="store_true", help="Fetch listings data from MLS service"
        )
        mgmt_cmd_lib.add_common_arguments(parser)

    def handle(self, cmd, rest, *args, **options):
        mgmt_cmd_lib.init(verbose=options["verbose"])
        logging.info(f"Running cmd = {cmd}, rest={rest}, options:\n{pprint.pformat(options)}")
        assert cmd == "eligible"
