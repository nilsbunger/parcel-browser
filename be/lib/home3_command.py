import logging
import sys

from django.core.management import BaseCommand

loggers_to_quiet = [
    "rasterio.env",
    "rasterio._env",
    "git.cmd",
    "shapely.geos",
    "matplotlib.pyplot",
    "matplotlib.font_manager",
]


class Home3Command(BaseCommand):
    """Override Django management command base class for Home3-specific behavior."""

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def create_parser(self, prog_name, subcommand, **kwargs):
        # add 'verbose' argument to all commands
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.add_argument("--verbose", action="store_true", help="Do verbose logging (DEBUG-level logging)")
        return parser

    def execute(self, *args, **options):
        # Add verbose logging as appropriate
        verbose = options["verbose"]
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if verbose else logging.INFO)

        logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)
        for logger in loggers_to_quiet:
            logging.getLogger(logger).setLevel(logging.INFO)
        logging.debug("DEBUG log level")
        logging.info("INFO log level")

        return super().execute(*args, **options)
