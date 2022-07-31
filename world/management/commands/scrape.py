from __future__ import annotations

import sys
from collections import defaultdict

from django.core.management import BaseCommand

from lib.analyze_parcel_lib import analyze_batch
from lib.crs_lib import get_utm_crs
from lib.listings_lib import listing_to_parcel
from lib.neighborhoods import Neighborhood
from lib.scraping_lib import scrape_san_diego_listings_by_zip_groups
from mygeo.util import eprint
from world.models import PropertyListing

LOCALHOST_MODE = False


class Command(BaseCommand):
    help = 'Scrape MLS Listings for San Diego and put updates into database'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        neighborhood_groups = [[Neighborhood.SDSU, Neighborhood.Miramesa],
                               # [Neighborhood.Clairemont, Neighborhood.OceanBeach],
                               # [Neighborhood.Encanto, Neighborhood.AlliedGardens],
                               ]

        # -----
        # 1. Scrape latest listings
        # -----
        zip_groups = []
        for hood_group in neighborhood_groups:
            hood_zips = [h for sublist in hood_group for h in sublist.value]
            zip_groups.append(hood_zips)

        stats = scrape_san_diego_listings_by_zip_groups(zip_groups, localhost_mode=LOCALHOST_MODE)

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
        listings = PropertyListing.objects.filter(status='ACTIVE')
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
                parcels_to_analyze.add(matched_parcel)
            # print("SAVED")
        print("DONE. Final stats associating parcels with listings:")
        print(dict(stats))

        # -----
        # 3. Generate parcel analysis for all the parcels
        # -----
        sd_utm_crs = get_utm_crs()
        results, errors = analyze_batch(
            parcels_to_analyze, zip_codes=[], utm_crs=sd_utm_crs, hood_name="listings", save_file=True
        )
        print ("HALLELUJAH")
        ### TODO: here's where item #1 from the July 30 H3-GIS feature needs should pick up.
