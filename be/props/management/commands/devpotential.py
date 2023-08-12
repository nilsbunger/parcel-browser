from datetime import date
import sys
import traceback
from typing import List

from ninja.errors import ValidationError

from elt.lib.standardize import ParcelFacts, SfHeFacts, RentBoardEntry, create_parcel_facts_csv
from elt.models import RawGeomData, RawSfParcelWrap
from lib.mgmt_lib import Home3Command
from lib.models_lib import group_queryset_by_field


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
        # zip_code = "94118"  # inner richmond

        # get all 2023 July rezoning concept housing element data
        qs = RawGeomData.objects.filter(juri="sf", data_type="he", run_date=date(2023, 7, 27)).order_by(
            "data__mapblklot"
        )
        he_count = qs.count()
        he_facts = dict()
        print("Processing Jul 2023 HE data")
        for idx, objgroup in enumerate(group_queryset_by_field(qs, "data__mapblklot")):
            if idx % 5000 == 0:
                print(f"Processing {idx}th item")
            # if idx == 100:
            #     break  # TODO: remove this
            x = SfHeFacts.from_orm(objgroup)
            he_facts[x.apn] = x
        print("Processing SF Parcels")
        print("Another line")
        qs = (
            RawSfParcelWrap.objects.filter(
                apn__in=list(he_facts.keys()), reportall_parcel__isnull=False
            )  # reportall_parcel__zip_code=zip_code)
            .select_related("parcel", "reportall_parcel", "he_table_a", "he_table_b")
            .prefetch_related("rawsfrentboardhousinginv_set")
        )
        print(f"Found {qs.count()} matching parcels for {he_count} HE records")
        # Attach he_facts to each parcel. Note, this is likely better done via a good query.
        for obj in qs:
            obj.he_facts = he_facts[obj.apn]
        try:
            facts: List[ParcelFacts] = [catch(ParcelFacts.from_orm, obj, idx=idx) for idx, obj in enumerate(qs)]
        except ValidationError as e:
            print(e)
            print(e.errors())
            raise
        create_parcel_facts_csv(facts, "sf_devpotential.csv")
        print("DONE")
