import csv
import sys
import traceback
from typing import List

from ninja.errors import ValidationError

from elt.lib.standardize import ParcelFacts
from elt.models import RawSfParcelWrap
from lib.mgmt_lib import Home3Command


def catch(func, *args, idx, raise_again=True, handle=lambda e: e, **kwargs):
    if idx % 1000 == 0:
        print(f"Processing {idx}th item")
    try:
        return func(*args, **kwargs)
    except Exception as e:
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)  # Fixed format
        print(e, file=sys.stderr)
        if raise_again:
            raise e
        return handle(e)


class Command(Home3Command):
    help = "Sort properties by development potential."

    def add_arguments(self, parser):
        pass
        # At some point we'll have multiple commands here.

    def handle(self, *args, **options):
        zip_code = "94118"  # inner richmond
        qs = RawSfParcelWrap.objects.filter(
            reportall_parcel__zip_code=zip_code, he_table_b_id__isnull=False
        ).select_related("parcel", "reportall_parcel", "he_table_a", "he_table_b")
        try:
            facts = [catch(ParcelFacts.from_orm, obj, idx=idx) for idx, obj in enumerate(qs)]
        except ValidationError as e:
            print(e)
            print(e.errors())
            raise
        print(facts[0])
        create_csv(facts, "sf_devpotential.csv")
        print("DONE")


def create_csv(schema_list: List, filename: str):
    fieldnames = vars(schema_list[0]).keys()

    # Create the CSV file
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in schema_list:
            row_dict = vars(row)
            writer.writerow(row_dict)
