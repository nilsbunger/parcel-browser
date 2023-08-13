import sys
import traceback
from datetime import date

from elt.lib.standardize import ParcelFacts, create_parcel_facts_csv
from elt.models import RawGeomData, RawSfParcelWrap
from lib.mgmt_lib import Home3Command
from ninja.errors import ValidationError


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
        # get APNs from all 2023 July rezoning concept housing element data - that's our universe
        apns = (
            RawGeomData.objects.filter(juri="sf", data_type="he", run_date=date(2023, 7, 27))
            .values_list("data__mapblklot", flat=True)
            .distinct()
        )

        print("Processing SF Parcels")
        qs = (
            RawSfParcelWrap.objects.filter(
                apn__in=list(apns), reportall_parcel__isnull=False
            )  # reportall_parcel__zip_code=zip_code)
            .select_related("parcel", "reportall_parcel", "he_table_a", "he_table_b")
            .prefetch_related("rawsfrentboardhousinginv_set")
            .prefetch_related("rawgeomdata_set")
        )
        print(
            f"Found {qs.count()} parcels for {len(apns)} HE APNs ({len(apns) - qs.count()} APNs from HE are missing)"
        )
        try:
            facts: list[ParcelFacts] = [
                catch(ParcelFacts.from_orm, obj, idx=idx) for idx, obj in enumerate(qs.iterator(chunk_size=2000))
            ]
        except ValidationError as e:
            print(e)
            print(e.errors())
            raise
        create_parcel_facts_csv(facts, "sf_devpotential.csv")
        print("DONE")
