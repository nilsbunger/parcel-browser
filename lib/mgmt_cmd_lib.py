import logging
import sys

loggers_to_quiet = [
    "rasterio.env",
    "rasterio._env",
    "git.cmd",
    "shapely.geos",
    "matplotlib.pyplot",
    "matplotlib.font_manager",
]


def init(verbose):
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if verbose else logging.INFO)

    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)
    for logger in loggers_to_quiet:
        logging.getLogger(logger).setLevel(logging.INFO)
    logging.debug("DEBUG log level")
    logging.info("INFO log level")


def add_common_arguments(parser):
    parser.add_argument(
        "--verbose", action="store_true", help="Do verbose logging (DEBUG-level logging)"
    )
