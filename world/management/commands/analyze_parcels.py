import operator
import pprint
from enum import Enum

from world.models import Parcel, AnalyzedParcel
from django.core.management.base import BaseCommand

from django.db import connection


class SubCommand(Enum):
    rebuild = 1
    histo = 2


class Command(BaseCommand):
    help = "Analyze all the residential parcels, creating or working with the analyze_parcels table"

    def add_arguments(self, parser):
        parser.add_argument("cmd", choices=SubCommand.__members__)
        pass

    def handle(self, cmd, *args, **options):
        self.pp = pprint.PrettyPrinter(indent=2)

        if cmd == "rebuild":
            self.rebuild()
        elif cmd == "histo":
            self.histo()
        else:
            self.stderr.write(self.style.FAIL("Unknown command %s" % cmd))

    def histo(self):

        histo_buckets = [0, 1, 5000, 6000, 7000, 8000, 10000, 15000, 22000, 40000, 100000, 300000]
        values = list()
        for bucket in histo_buckets:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"select count(lot_size) from world_analyzedparcel where"
                    f"lot_size >= {bucket} and skip is false"
                )
                row = cursor.fetchone()
            print(row[0])
            values.append([bucket, int(row[0])])
        # currently the histo buckets have all values GREATER than the lot size, including bigger histo buckets.
        # So patch up the list.
        print(values)
        for i in range(len(values) - 1):
            values[i][1] -= values[i + 1][1]
        print(values)
        print(type(values[0][0]), type(values[0][1]))
        self.ascii_histogram(values)

    def ascii_histogram(self, values):
        """A horizontal frequency-table/histogram plot."""
        max = 0
        for i in values:
            if i[1] > max:
                max = i[1]
        for k in values:
            scale = int(40 * k[1] / max)
            print("{0:6d} {1:8d} : {2}".format(k[0], k[1], "+" * scale))

    # Rebuild analyzed_parcel table, which keeps track of which parcels we've ruled out for various reasons
    def rebuild(self):
        # Query that finds all APNs with R1-like zoning
        selfields = (
            "apn, world_parcel.id, usable_sq_field, total_lvg_field, acreage,"
            "zone_name, ordnum, nucleus_us, situs_juri, OVERLAY_JU"
        )
        query = (
            "select distinct on(apn)"
            + selfields
            + " from world_parcel, world_zoningbase \
                WHERE zone_name LIKE 'RS-1-%%' and ST_Intersects(world_parcel.geom, world_zoningbase.geom);"
        )
        # count_query = "select count(apn) from (" + query + ") AS foo;"

        parcels = Parcel.objects.raw(query)

        include_count = 0
        skip_count = dict({})
        assert (
            False
        ), "This uses an old version of AnalyzedParcel schema... it's defunct and replaced by dataprep cmd"
        for idx, parcel in enumerate(parcels):
            if idx % 1000 == 0:
                print("Processing # %d" % idx)
            lot_size = parcel.acreage * 44000 if parcel.acreage else parcel.usable_sq_field
            if not lot_size:
                lot_size = 0
            lot_size = int(lot_size)
            skip_reason = ""
            nucleus_us = int(parcel.nucleus_us or 0)
            if nucleus_us < 100 or nucleus_us > 118:
                skip_reason = "NUCLEUS_" + str(nucleus_us)
            elif parcel.overlay_ju != "SD":
                skip_reason = "JURISDICTION_" + str(parcel.overlay_ju)
            # Evaluate lot sizes after other reasons, since lot size 0 may mean it's a townhouse or something
            elif lot_size == 0:
                skip_reason = "LOT_ZERO"
            elif lot_size < 2400:
                skip_reason = "LOT_UNDER_2_4K"
            elif lot_size < 5000:
                skip_reason = "LOT_UNDER_5K"

            if skip_reason:
                skip_count[skip_reason] = skip_count.get(skip_reason, 0) + 1
                if idx % 100 == 0:
                    print(parcel.__dict__)
                    print(skip_reason)

            else:
                include_count += 1
            AnalyzedParcel.objects.update_or_create(
                apn=parcel.apn,
                defaults={
                    "lot_size": lot_size,
                    "building_size": parcel.total_lvg_field,
                    "skip": skip_reason != "",
                    "skip_reason": skip_reason,
                },
            )
        print("Included %d parcels" % include_count)
        sorted_skips = sorted(skip_count.items(), key=operator.itemgetter(1), reverse=True)

        print("Skipped:")
        print(self.pp.pprint(sorted_skips))
        self.stdout.write(self.style.SUCCESS("Finished running analyze_parcels"))
