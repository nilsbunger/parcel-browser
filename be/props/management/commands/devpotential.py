import csv
import sys
import traceback
from typing import List

from more_itertools import collapse
from ninja.errors import ValidationError

from elt.lib.standardize import ParcelFacts, RentBoardEntry
from elt.models import RawSfParcelWrap
from lib.mgmt_lib import Home3Command


def catch(func, *args, idx, raise_again=True, handle=lambda e: e, **kwargs):
    if idx % 100 == 0:
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
        qs = (
            RawSfParcelWrap.objects.filter(reportall_parcel__zip_code=zip_code, he_table_b_id__isnull=False)
            .select_related("parcel", "reportall_parcel", "he_table_a", "he_table_b")
            .prefetch_related("rawsfrentboardhousinginv_set")
        )

        try:
            facts: List[ParcelFacts] = [catch(ParcelFacts.from_orm, obj, idx=idx) for idx, obj in enumerate(qs)]
        except ValidationError as e:
            print(e)
            print(e.errors())
            raise
        create_parcel_facts_csv(facts, "sf_devpotential.csv")
        print("DONE")


def create_parcel_facts_csv(schema_list: List[ParcelFacts], filename: str):
    """Create a CSV file from a list of ParcelFacts objects, including relevant related data.
    This should be similar to the data we'd show in a detailed parcel view."""
    fieldnames = list(schema_list[0].dict().keys())
    fieldnames.remove("rent_board_data")
    fieldnames += collapse(
        [
            (f"contact_name{i}", f"contact_email{i}", f"contact_phone{i}", f"contact_role{i}", f"contact_type{i}")
            for i in [1, 2, 3, 4]
        ]
    )

    # Create the CSV file
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore", restval=None)

        writer.writeheader()
        for row in schema_list:
            row_dict = dict(vars(row))  # dict() to make a copy
            if row.rent_board_data:
                deduped_contacts = set(
                    (r.contact_name, r.contact_email, r.contact_phone, r.contact_role, r.contact_type)
                    for r in row.rent_board_data
                    if r.contact_name
                )
                for i, contact in enumerate(list(deduped_contacts)[:4], start=1):
                    row_dict[f"contact_name{i}"] = contact[0]
                    if contact[0] == "Vesta Asset Management":
                        print("found Vesta Asset Management")
                    row_dict[f"contact_email{i}"] = contact[1]
                    row_dict[f"contact_phone{i}"] = contact[2]
                    row_dict[f"contact_role{i}"] = contact[3].label if contact[3] else None
                    row_dict[f"contact_type{i}"] = contact[4].label if contact[4] else None
            writer.writerow(row_dict)
