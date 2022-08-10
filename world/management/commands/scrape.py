from __future__ import annotations

from collections import defaultdict
from datetime import date
import pprint
import random
import sys
import logging
from django.core.management import BaseCommand
from pandas import DataFrame

from lib.analyze_parcel_lib import analyze_batch
from lib.crs_lib import get_utm_crs
from lib.listings_lib import listing_to_parcel
from lib.neighborhoods import AllSdCityZips, Neighborhood
from lib.scraping_lib import scrape_san_diego_listings_by_zip_groups
from mygeo.util import eprint
from world.models import PropertyListing


# NOTE: We should rename this command to 'listings', since it generally does ingest operations on MLS listings
def zip_groups_by_neighborhood():
    neighborhood_groups = [[Neighborhood.SDSU, Neighborhood.Miramesa],
                           [Neighborhood.Clairemont, Neighborhood.OceanBeach],
                           [Neighborhood.Encanto, Neighborhood.AlliedGardens],
                           [Neighborhood.PacificBeach]
                           ]
    zip_groups = []
    for hood_group in neighborhood_groups:
        hood_zips = [
            h for sublist in hood_group for h in sublist.value]
        zip_groups.append(hood_zips)
    return zip_groups


def zip_groups_from_zips(zips):
    # Take a list of zip codes, and turn them into a random groups of variable # of zips for querying against.
    zips = zips.copy()
    # Make zipcode list stable for all runs in one day for debugging, by using a random seed based on date.
    ordinal_date = date.today().toordinal()
    rand = random.Random(ordinal_date)
    rand.shuffle(zips)
    zip_groups = []
    while zips:
        num = min(rand.randint(2, 4), len(zips))
        zip_group = [zips.pop() for i in range(num)]
        zip_groups.append(zip_group)
    print(zip_groups)
    return zip_groups


class Command(BaseCommand):
    help = 'Parse MLS Listings for San Diego, analyze, and put into database. Optionally re-scrape'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fetch', action='store_true', help="Fetch listings data from MLS service"
        )
        parser.add_argument(
            '--fetch-zip',
            action='store', help="Fetch listings for ONE specified zip from cache (if available) or MLS service"
        )
        parser.add_argument(
            '--fetch-local', action='store_true',
            help="Fetch listings from localhost. Useful to see request stream, but it won't generate useful responses"
        )
        parser.add_argument(
            '--verbose', action='store_true', help="Do verbose logging (DEBUG-level logging)"
        )
        parser.add_argument(
            '--no-cache', action='store_true', help="Don't use existing cached query data even if it's available"
        )
        parser.add_argument(
            '--skip-analysis', action='store_true', help="Don't run parcel analysis"
        )

    def handle(self, *args, **options):
        logging.getLogger().setLevel('DEBUG' if options['verbose'] else 'INFO')
        logging.debug("log level set")

        # -----
        # 1. Scrape latest listings if directed to.
        # -----

        if options['fetch'] or options['fetch_local'] or options['fetch_zip']:
            zip_groups = [[options['fetch_zip']]] if options['fetch_zip'] else zip_groups_from_zips(AllSdCityZips)
            logging.info(
                f'Fetching {len(zip_groups)} groups of zip codes. Local={options["fetch_local"] is True}, Cache={options["no_cache"] is False}')
            stats = scrape_san_diego_listings_by_zip_groups(
                zip_groups, localhost_mode=options['fetch_local'], cache=not options['no_cache'])

            logging.info(f'\nCRAWLER DONE.\nFound {stats.get_value("listing/no_change")} entries with no change, '
                         f' {stats.get_value("listing/new_or_update")} new or updated')
            logging.info(f'{stats.get_value("response_received_count")} responses received'
                         f' (of which, {stats.get_value("httpcache/hit")} were from CACHE)')
            error_pages = stats.get_value('httperror/response_ignored_count')
            sys.stdout.flush()
            if error_pages:
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
        logging.info(f'Found {len(listings)} properties to associate')
        for l in listings:
            # print(f"Working on {l.addr}")
            matched_parcel, error = listing_to_parcel(l)
            if error:
                stats[error] += 1
            else:
                # Got matched parcel, record the foreign key link in the listing.
                stats['success'] += 1
                l.parcel = matched_parcel
                l.save(update_fields={'parcel'})
                zipcode = matched_parcel.situs_zip
                if matched_parcel.situs_juri == 'SD':
                    parcels_to_analyze.add((matched_parcel, l))
                    zipcode = matched_parcel.situs_zip
                    if zipcode:
                        stats[f'info_sd_{zipcode[0:5]}'] += 1
                        if int(zipcode[0:5]) not in AllSdCityZips:
                            stats[f'error_city_zip_{zipcode[0:5]}_missing'] += 1
                    else:
                        stats[f'info_sd_unknown_zip'] += 1
                else:
                    if zipcode:
                        if int(zipcode[0:5]) in AllSdCityZips:
                            # print(f"Skipping {matched_parcel.situs_addr} {matched_parcel.situs_stre}, {zip[0:5]}."
                            #       f"It's in jurisdiction={matched_parcel.situs_juri}, NOT in SD City")
                            stats[
                                f'error_city_zip_with_non_city_jurisdiction_{zipcode[0:5]}_{matched_parcel.situs_juri}'] += 1
                        else:
                            stats[f'info_skipping_non_city_zip{zipcode[0:5]}_{matched_parcel.situs_juri}'] += 1
            # print("SAVED")
        logging.info("DONE. Final stats associating parcels with listings:")
        pprint.pprint(dict(stats))

        # -----
        # 3. Generate parcel analysis for all the parcels if directed to
        # -----
        if options['skip_analysis']:
            logging.info("SKIPPING parcel analysis")
        else:
            parcels, parcel_listings = zip(*parcels_to_analyze)
            sd_utm_crs = get_utm_crs()
            results, errors = analyze_batch(
                parcels, zip_codes=[], utm_crs=sd_utm_crs, hood_name="listings", save_file=True,
                save_dir="./frontend/static/temp_computed_imgs", save_as_model=True, listings=parcel_listings)

            # Save the errors to a csv
            error_df = DataFrame.from_records(errors)
            error_df.to_csv(
                "./frontend/static/temp_computed_imgs/errors.csv", index=False)

            logging.info(
                f"Analysis done! There are {len(results)} successes and {len(errors)} errors.")
