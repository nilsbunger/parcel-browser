import logging
import sys
from collections import defaultdict
from pprint import pprint

from django.core.management.base import BaseCommand
from django.core.serializers import serialize

from elt.models import RawSfParcelWrap

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dumps ELT fixtures used in tests from Raw** models"

    def handle(self, *args, **options):
        """Filter a set of interesting parcels for test fixtures. Get ~3 per zoning code, scoped to one zip code.."""
        # Use like this: ./manage.py elt_dump > elt/tests/fixtures/elt_dump.json
        # Sort querysets so that results are reproducible
        # zoning_codes = ("NCD|RH-2", "NC-2", "NC-3", "RH-1|RM-1", "RM-3", "NC-1", "RM-2", "NC-S", "RH-3")
        # zoning_codes += ("RH-1(D)", "NCD", "RM-1", "RH-1", "RH-2")
        zip_code = "94118"  # inner richmond
        entries_per_zoning_code = 2
        related_fields = ("parcel", "reportall_parcel", "he_table_a", "he_table_b")
        many_to_one_fields = ("rawsfrentboardhousinginv",)
        # Filter parcels within a zip code and with a housing element table B entry and w/ rentboard data.
        qs_unordered = RawSfParcelWrap.objects.filter(
            reportall_parcel__zip_code=zip_code, he_table_b_id__isnull=False, rawsfrentboardhousinginv__isnull=False
        )
        zoning_codes = list(qs_unordered.values_list("parcel__zoning_cod", flat=True).distinct())
        print(f"Found zoning codes: {zoning_codes} in zip code {zip_code}", file=sys.stderr)
        qs = qs_unordered.order_by("apn")
        pprint(f"Found {len(qs)} parcels in {zip_code} w/ housing element and rent board data", stream=sys.stderr)
        # filter the queryset down to N entries per zoning code.
        parcels_by_zone = defaultdict(list)
        for parcel_wrap in qs:
            parcels_by_zone[parcel_wrap.parcel.zoning_cod].append(parcel_wrap)
        # limit the dict to N entries per zone
        parcels_by_zone = {k: v[0:entries_per_zoning_code] for k, v in parcels_by_zone.items()}
        pprint(f"Limited parcels_by_zone:", stream=sys.stderr)
        pprint([f"{zone}:{[p.pk for p in parcels]}" for zone, parcels in parcels_by_zone.items()], stream=sys.stderr)

        # flatten the dict into a list of parcel_wraps
        obj_list = []
        for _zone, parcel_wrap_list in parcels_by_zone.items():
            obj_list += parcel_wrap_list
        print("Limited parcelwrap list length: ", len(obj_list), file=sys.stderr)
        # get related objects and add them to the list to be serialized.
        related_list = []
        for fieldname in related_fields:
            related_pks = {getattr(pwrap, fieldname + "_id") for pwrap in obj_list}
            related_model_cls = getattr(RawSfParcelWrap, fieldname).field.related_model
            related_list.extend(list(related_model_cls.objects.filter(pk__in=related_pks).order_by("pk")))
        print(f"Related list length from {related_fields}: ", len(related_list), file=sys.stderr)
        # get related objects that are related by the  and add them to the list to be serialized.
        many_to_one_list = []
        for fieldname in many_to_one_fields:
            field_obj = obj_list[0]._meta.get_field(fieldname)
            related_model_cls = field_obj.related_model
            qs = related_model_cls.objects.filter(rawsfparcelwrap__in=obj_list).order_by("rawsfparcelwrap")
            many_to_one_list.extend(list(qs))
        print(f"Many-to-one list length from {many_to_one_fields}: ", len(many_to_one_list), file=sys.stderr)
        # serialize it all.
        parcel_wrap_json = serialize("json", obj_list + related_list + many_to_one_list)
        sys.stdout.write(parcel_wrap_json)

        # convert json to a list of dicts
        # parcel_wrap_list = eval(parcel_wrap_json)
        print("DONE", file=sys.stderr)
