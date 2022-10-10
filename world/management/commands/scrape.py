from __future__ import annotations

from collections import Counter, defaultdict
import datetime
import logging
import pprint
import random
import sys
import tempfile
from typing import List

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from pandas import DataFrame

from lib import mgmt_cmd_lib
from lib.analyze_parcel_lib import analyze_batch
from lib.crs_lib import get_utm_crs
from lib.listings_lib import address_to_parcel
from lib.neighborhoods import AllSdCityZips, Neighborhood
from lib.scraping_lib import scrape_san_diego_listings_by_zip_groups
from mygeo import settings
from mygeo.util import eprint
from world.models import Parcel, PropertyListing


# NOTE: We should rename this command to 'listings', since it generally does ingest operations on MLS listings
def zip_groups_by_neighborhood():
    neighborhood_groups = [
        [Neighborhood.SDSU, Neighborhood.Miramesa],
        [Neighborhood.Clairemont, Neighborhood.OceanBeach],
        [Neighborhood.Encanto, Neighborhood.AlliedGardens],
        [Neighborhood.PacificBeach],
    ]
    zip_groups = []
    for hood_group in neighborhood_groups:
        hood_zips = [h for sublist in hood_group for h in sublist.value]
        zip_groups.append(hood_zips)
    return zip_groups


def zip_groups_from_zips(zips):
    # Take a list of zip codes, and turn them into a random groups of variable # of zips for querying against.
    zips = zips.copy()
    # Make zipcode list stable for all runs in one day for debugging, by using a random seed based on date.
    ordinal_date = datetime.date.today().toordinal()
    rand = random.Random(ordinal_date)
    rand.shuffle(zips)
    zip_groups = []
    while zips:
        num = min(rand.randint(3, 5), len(zips))
        zip_group = [zips.pop() for i in range(num)]
        zip_groups.append(zip_group)
    print(zip_groups)
    return zip_groups


class Command(BaseCommand):
    help = "Parse MLS Listings for San Diego, analyze, and put into database. Optionally re-scrape"

    def add_arguments(self, parser):
        mgmt_cmd_lib.add_common_arguments(parser)
        parser.add_argument(
            "--fetch", action="store_true", help="Fetch listings data from MLS service"
        )
        parser.add_argument(
            "--fetch-zip",
            action="store",
            help="Fetch listings for ONE specified zip from cache (if available) or MLS service",
        )
        parser.add_argument(
            "--fetch-local",
            action="store_true",
            help="Fetch listings from localhost. Useful to see request stream, but it won't generate useful responses",
        )
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Don't use existing cached data even if it's available (both for scraping and for analysis)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't store analysis to the database (not, it doesn't control scraping (aka fetching) at the moment)",
        )
        parser.add_argument(
            "--skip-matching",
            action="store_true",
            help="Don't run listing-to-address matching (also skips parcel analysis)",
        )
        parser.add_argument(
            "--skip-analysis", action="store_true", help="Don't run parcel analysis"
        )
        parser.add_argument(
            "--parcel", action="store", help="Run analysis only (no scrape) on a single parcel"
        )
        parser.add_argument(
            "--single-process", action="store_true", help="Run analysis with only a single process"
        )

    def handle(self, *args, **options):
        mgmt_cmd_lib.init(verbose=options["verbose"])
        # -----
        # 1. Scrape latest listings if directed to.
        # -----

        if options["fetch"] or options["fetch_local"] or options["fetch_zip"]:
            if settings.LOCAL_DB:
                logging.warning("Fetching with local DB???? Type 'yes' to confirm this craziness")
                value = input("Go ahead:")
                if value != "yes":
                    logging.info("Exiting")
                    sys.exit(1)

            zip_groups = (
                [[options["fetch_zip"]]]
                if options["fetch_zip"]
                else zip_groups_from_zips(AllSdCityZips)
            )
            logging.info(
                f'Fetching {len(zip_groups)} groups of zip codes. Local={options["fetch_local"] is True}, Cache={options["no_cache"] is False}'
            )
            stats = scrape_san_diego_listings_by_zip_groups(
                zip_groups, localhost_mode=options["fetch_local"], cache=not options["no_cache"]
            )

            logging.info(
                f'\nCRAWLER DONE.\nFound {stats.get_value("listing/no_change")} entries with no change, '
                f' {stats.get_value("listing/new_or_update")} new or updated'
            )
            logging.info(
                f'{stats.get_value("response_received_count")} responses received'
                f' (of which, {stats.get_value("httpcache/hit")} were from CACHE)'
            )
            error_pages = stats.get_value("httperror/response_ignored_count")
            sys.stdout.flush()
            if error_pages:
                eprint(f"!! {error_pages} error responses")

        # ----
        # 1.5 Look for old listings that aren't active anymore
        if not options["parcel"]:
            stale_stats = PropertyListing.mark_all_stale(days_for_stale=5)
            logging.info(f"\n\nSTALE LISTINGS REPORT: {stale_stats}")

        # -----
        # 2. Associate listings with parcels
        # -----
        stats = defaultdict(int)
        parcels_to_analyze = set()
        if options["skip_matching"] or options["parcel"]:
            logging.info("SKIPPING matching of listings to parcels")
        else:
            logging.info(f"Running matching")

            prop_listings = PropertyListing.active_listings_queryset().prefetch_related(
                "analyzedlisting", "parcel"
            )
            logging.info(f"Found {len(prop_listings)} properties to associate")
            for prop_listing in prop_listings:
                try:
                    # If we're caching and the parcel, and analyzed listing exists, we can skip analysis and
                    # go to the next listing.
                    if (
                        not options["no_cache"]
                        and prop_listing.parcel
                        and prop_listing.analyzedlisting
                    ):
                        stats[f"info_previously_matched"] += 1
                        continue
                except ObjectDoesNotExist as e:
                    # we're missing a relationship, so we need to analyze this parcel.
                    pass
                matched_parcel, error = address_to_parcel(prop_listing.addr, jurisdiction="SD")
                if error:
                    stats[error] += 1
                else:
                    # Got matched parcel, record the foreign key link in the listing.
                    stats["success"] += 1
                    prop_listing.parcel = matched_parcel
                    prop_listing.save(update_fields={"parcel"})
                    zipcode = matched_parcel.situs_zip
                    if matched_parcel.situs_juri == "SD":
                        parcels_to_analyze.add((matched_parcel, prop_listing))
                        zipcode = matched_parcel.situs_zip
                        if zipcode:
                            stats[f"info_sd_{zipcode[0:5]}"] += 1
                            if int(zipcode[0:5]) not in AllSdCityZips:
                                stats[f"error_city_zip_{zipcode[0:5]}_missing"] += 1
                        else:
                            stats[f"info_sd_unknown_zip"] += 1
                    else:
                        if zipcode:
                            if int(zipcode[0:5]) in AllSdCityZips:
                                # print(f"Skipping {matched_parcel.situs_addr} {matched_parcel.situs_stre}, {zip[0:5]}."
                                #       f"It's in jurisdiction={matched_parcel.situs_juri}, NOT in SD City")
                                stats[
                                    f"error_city_zip_with_non_city_jurisdiction_{zipcode[0:5]}_{matched_parcel.situs_juri}"
                                ] += 1
                            else:
                                stats[
                                    f"info_skipping_non_city_zip{zipcode[0:5]}_{matched_parcel.situs_juri}"
                                ] += 1
                # print("SAVED")
            logging.info("DONE. Final stats associating parcels with listings:")
            logging.info(pprint.pformat(dict(stats)))

        # -----
        # 3. Generate parcel analysis for all the parcels if directed to
        # -----
        if options["skip_analysis"] or options["skip_matching"]:
            logging.info("SKIPPING parcel analysis")
        else:
            if options["parcel"]:
                # Run on single parcel
                parcels = [Parcel.objects.get(apn=options["parcel"])]
                property_listings: List[PropertyListing] = [
                    PropertyListing.active_listings_queryset()
                    .filter(parcel=parcels[0])
                    .latest("seendate")
                ]
            else:
                # Run on batch
                parcels: List[Parcel]
                property_listings: List[PropertyListing]
                parcels, property_listings = zip(*parcels_to_analyze)
            logging.info(f"Running parcel analysis on {len(property_listings)} listings")
            sd_utm_crs = get_utm_crs()
            # NOTE: Make sure changes to the call here are also made in api.redo_analysis
            with tempfile.TemporaryDirectory() as tmpdirname:
                results, errors = analyze_batch(
                    parcels,
                    sd_utm_crs,
                    property_listings,
                    options["dry_run"],
                    save_dir=tmpdirname,
                    single_process=bool(options["parcel"]) or bool(options["single_process"]),
                )

            # Save the errors to a csv
            error_df = DataFrame.from_records(errors)
            error_df.to_csv("./frontend/static/temp_computed_imgs/errors.csv", index=False)
            stats = Counter({})
            for result in results:
                stats += result.details["messages"]["stats"]
            logging.info("Aggregated Stats:")
            logging.info(dict(stats))
            logging.info(
                f"Analysis done! There are {len(results)} successes and {len(errors)} errors."
            )
