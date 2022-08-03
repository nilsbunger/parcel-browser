from __future__ import annotations

import sys
import os
from collections import defaultdict

from django.core.management import BaseCommand
from pandas import DataFrame

from lib.analyze_parcel_lib import analyze_batch
from lib.crs_lib import get_utm_crs
from lib.listings_lib import listing_to_parcel
from lib.neighborhoods import Neighborhood
from lib.scraping_lib import scrape_san_diego_listings_by_zip_groups
from mygeo.util import eprint
from world.models import PropertyListing


# NOTE: We should rename this command to 'listings', since it generally does ingest operations on MLS listings

class Command(BaseCommand):
    help = 'Parse MLS Listings for San Diego, analyze, and put into database. Optionally re-scrape'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fetch', action='store_true', help="Fetch listings data from MLS service"
        )
        parser.add_argument(
            '--fetch-local', action='store_true',
            help="Fetch listings from localhost. Useful to see request stream, but it won't generate useful responses"
        )
        parser.add_argument(
            '--no-cache', action='store_true', help="Don't cache existing query data"
        )
        parser.add_argument(
            '--skip-analysis', action='store_true', help="Don't run parcel analysis"
        )

    def handle(self, *args, **options):
        # Group neighborhoods together into meaningful fetch groups. Each entry in top-level list turns into one
        # fetch.
        neighborhood_groups = [[Neighborhood.SDSU, Neighborhood.Miramesa],
                               [Neighborhood.Clairemont, Neighborhood.OceanBeach],
                               [Neighborhood.Encanto, Neighborhood.AlliedGardens],
                               ]

        # -----
        # 1. Scrape latest listings if directed to.
        # -----
        if options['fetch'] or options['fetch_local']:
            print("Fetching from MLS service")
            zip_groups = []
            for hood_group in neighborhood_groups:
                hood_zips = [
                    h for sublist in hood_group for h in sublist.value]
                zip_groups.append(hood_zips)

            stats = scrape_san_diego_listings_by_zip_groups(
                zip_groups, localhost_mode=options['fetch_local'], cache=not options['no_cache'])

            print(f'\nCRAWLER DONE.\nFound {stats.get_value("listing/no_change")} entries with no change, '
                  f' {stats.get_value("listing/new_or_update")} new or updated')
            print(f'{stats.get_value("response_received_count")} responses received'
                  f' (of which, {stats.get_value("httpcache/hit")} were from CACHE)')
            error_pages = stats.get_value('httperror/response_ignored_count')
            sys.stdout.flush()
            if (error_pages):
                eprint(f'!! {error_pages} error responses')

        # -----
        # 2. Associate listings with parcels
        # -----

        # Associate parcel IDs where possible
        listings = PropertyListing.objects.filter(
            status__in=['ACTIVE', 'OFFMARKET'])

        # A set of tuples (parcel, listing)
        parcels_to_analyze = set()
        stats = defaultdict(int)
        print(f'Found {len(listings)} properties to associate')
        for l in listings:
            # print(f"Working on {l.addr}")
            matched_parcel, error = listing_to_parcel(l)
            if error:
                stats[error] += 1
            else:
                stats['success'] += 1
                # Got matched parcel, record the foreign key link in the listing.
                l.parcel = matched_parcel
                l.save(update_fields={'parcel'})
                parcels_to_analyze.add((matched_parcel, l))
            # print("SAVED")
        print("DONE. Final stats associating parcels with listings:")
        print(dict(stats))

        if options['skip_analysis']:
            print("SKIPPING parcel analysis / generating picklefile")
        else:
            # -----
            # 3. Generate parcel analysis for all the parcels
            # -----
            parcels, parcel_listings = zip(*parcels_to_analyze)
            sd_utm_crs = get_utm_crs()
            results, errors = analyze_batch(
                parcels, zip_codes=[], utm_crs=sd_utm_crs, hood_name="listings", save_file=True,
                save_dir="./frontend/static/temp_computed_imgs", save_as_model=True, listings=parcel_listings)

        print(
            f"We're done! There are {len(results)} successes and {len(errors)} errors.")
