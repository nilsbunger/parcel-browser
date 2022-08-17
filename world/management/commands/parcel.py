import pprint
from collections import OrderedDict
from enum import Enum
from lib.analyze_parcel_lib import analyze_by_apn, analyze_batch
from lib.crs_lib import get_utm_crs

from django.core.management.base import BaseCommand
from lib.neighborhoods import Neighborhood
from lib.parcel_lib import get_parcels_by_zip_codes


class Command(BaseCommand):
    help = 'Analyze a parcel and generate scenarios'

    def add_arguments(self, parser):
        parser.add_argument('--apn', '-a', action='store',
                            help="APN of parcel to analyze")
        parser.add_argument('--neighborhood', '-n', action='store',
                            help="Specifies a neighborhood to analyze")
        parser.add_argument(
            '--show-plot', '-p', action='store_true', help="Display the plot on a GUI")
        parser.add_argument('--save-file', '-f', action='store_true',
                            help="Save the plot images to a file")
        parser.add_argument('--save-dir', action='store',
                            help='Specify a custom directory to save files to.'
                                 'If none is provided, the default is used')
        parser.add_argument('--limit', '-l', action='store',
                            help="Limit the number of parcels analyzed")
        parser.add_argument('--shuffle', '-s', action='store_true',
                            help="Shuffle the parcels")
        # Maybe this option isn't needed, I don't think the lot split calculation is
        # very expensive at all. Might even be negligible.
        parser.add_argument('--skip-lot-splits', action='store_true',
                            help="Skip calculating lot splits. May be computationally better, but only slightly")

    def handle(self, *args, **options):
        sd_utm_crs = get_utm_crs()
        if options['apn']:
            results = analyze_by_apn(options['apn'],
                                     sd_utm_crs,
                                     show_plot=options['show_plot'],
                                     save_file=options['save_file'])
            results =OrderedDict({k: v for (k, v) in results.items() if k not in
                       ['buildings', 'no_build_zones', 'datetime_ran', 'avail_geom', 'git_commit_hash']})

            pprint.pprint(results)
        elif options['neighborhood']:
            parcels = list(get_parcels_by_zip_codes(Neighborhood[options['neighborhood']].value))
            analyze_batch(parcels=parcels,
                          utm_crs=sd_utm_crs,
                          hood_name=options['neighborhood'],
                          save_file=options['save_file'],
                          save_dir=options['save_dir'],
                          limit=options['limit'],
                          shuffle=options['shuffle'],
                          try_split_lot=not options['skip_lot_splits'])
        else:
            print("Failed. Please specify either an APN or a neighborhood")
