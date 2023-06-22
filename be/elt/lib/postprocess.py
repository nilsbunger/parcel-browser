from django.contrib.gis.db import models
from django.db.models import Count
from django.forms import model_to_dict

from elt.models import RawSfHeTableA, RawSfHeTableB, RawSfParcel
from elt.models.raw_sf_parcel_wrap import RawSfParcelWrap
from parsnip.util import dict_del_keys


def postprocess_sf():
    """After loading raw data, this method does post-processing like:
    - creating the RawSfParcelWrap model
    - any other checks and post-processing to be identified
    """
    same_count = 0
    # check RawSfParcel for duplicates (ie same mapblklot); check if those duplicates have same data.
    model: models.Model
    for model, field in [(RawSfHeTableA, "mapblklot"), (RawSfHeTableB, "mapblklot"), (RawSfParcel, "blklot")]:
        dupes = model.objects.values(field).annotate(Count("id")).order_by().filter(id__count__gt=1)
        print(f"Working on {len(dupes)} duplicates in {model}...")
        # check if the parcels have same data (except for id)
        for dupe in dupes:
            dupe_models = model.objects.filter(**{field: dupe[field]})
            objs = [model_to_dict(m) for m in dupe_models]
            if len(dupe_models) > 1:
                for i in range(len(objs) - 1):
                    if dict_del_keys(objs[i], ["id"]) != dict_del_keys(objs[i + 1], ["id"]):
                        print(f"Parcels {objs[i]['id']} and {objs[i + 1]['id']} have different data")
                    else:
                        same_count += 1
                        model.objects.filter(pk=objs[i]["id"]).delete()
    print("Deleted {} duplicates with same data".format(same_count))
    print("\nMatching APNs in RawSfParcel (blklot), RawSfHeTableA (mapblklot), and RawSfHeTableB(mapblklot)...")
    parcel_apns = set(RawSfParcel.objects.values_list("blklot", flat=True))
    table_a_apns = set(RawSfHeTableA.objects.values_list("mapblklot", flat=True))
    table_b_apns = set(RawSfHeTableB.objects.values_list("mapblklot", flat=True))
    print(f"Found {len(parcel_apns)} apns in RawSfParcel")
    print(f"Found {len(table_a_apns)} apns in RawSfHeTableA")
    print(f"Found {len(table_b_apns)} apns in RawSfHeTableB")

    # get set of items in table_a_apns but not in parcel_apns
    table_a_unknown_apns = table_a_apns - parcel_apns
    table_b_unknown_apns = table_b_apns - parcel_apns

    print(f"{len(table_a_unknown_apns)} unmatched apns in table_a")
    print(f"{len(table_b_unknown_apns)} unmatched apns in table_b")

    parcels = RawSfParcel.objects.all()

    # Create RawSfParcelWrap objects for each parcel
    wrap_objects = []
    wrap_update_fields = {f.name for f in RawSfParcelWrap._meta.fields} - {"apn"}
    for parcel in parcels:
        # Get associated he_table_a and he_table_b entries. Sort by run_date so most recent is first, and take that
        # entry.

        he_table_a = RawSfHeTableA.objects.filter(mapblklot=parcel.blklot).order_by("-run_date").first()
        he_table_b = RawSfHeTableB.objects.filter(mapblklot=parcel.blklot).order_by("-run_date").first()

        # Create RawSfParcelWrap object
        wrap = RawSfParcelWrap(apn=parcel.blklot, parcel=parcel, he_table_a=he_table_a, he_table_b=he_table_b)
        # Accumulate wrap objects and then bulk_create 1000 of them at a time
        wrap_objects.append(wrap)
        if len(wrap_objects) >= 100:
            # create with fallback to update existing entries (updating all fields besides apn)
            RawSfParcelWrap.objects.bulk_create(
                wrap_objects, update_conflicts=True, unique_fields=["apn"], update_fields=wrap_update_fields
            )
            wrap_objects = []
            print(".", end="", flush=True)
    # Bulk create any remaining wrap objects
    RawSfParcelWrap.objects.bulk_create(
        wrap_objects, update_conflicts=True, unique_fields=["apn"], update_fields=wrap_update_fields
    )
    wrap_objects = []
    print("DONE")
