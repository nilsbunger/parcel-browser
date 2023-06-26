from django.contrib.gis.db import models
from django.db.models import Count, F, Max, OuterRef, QuerySet, Subquery, Window
from django.db.models.functions import RowNumber
from django.forms import model_to_dict

from elt.models import RawSfHeTableA, RawSfHeTableB, RawSfParcel, RawSfReportall
from elt.models.raw_sf_parcel_wrap import RawSfParcelWrap
from parsnip.util import dict_del_keys


def check_for_dupes_sf():
    """Check for duplicates in RawSfParcel, RawSfHeTableA, and RawSfHeTableB, and remove if found."""
    same_count = 0
    # check RawSfParcel for duplicates (ie same mapblklot); check if those duplicates have same data.
    model: models.Model
    print("Checking for duplicates in RawSfParcel, RawSfHeTableA, and RawSfHeTableB...")
    for model, field in [(RawSfHeTableA, "mapblklot"), (RawSfHeTableB, "mapblklot"), (RawSfParcel, "blklot")]:
        # get duplicates (same APN and run_date) by annotating apn and run_date, then aggregating with count.
        dupes = model.objects.values(field, "run_date").annotate(foo=Count("id")).filter(foo__gt=1)
        if len(dupes) > 0:
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
    if same_count > 0:
        print("Deleted {} duplicates with same data".format(same_count))
    else:
        print("No duplicates found")


def check_parcel_wraps_sf():
    """Check we have a parcel wrap entity for each parcel. If any are missing, create them."""
    print("Checking completeness of parcel wrap entities...")
    parcels = RawSfParcel.objects.only("blklot").all()
    parcel_wraps = RawSfParcelWrap.objects.only("apn").all()
    print(f"Found {len(parcels)} parcels and {len(parcel_wraps)} parcel wraps")
    parcel_apns = {parcel.blklot for parcel in parcels}
    parcel_wrap_apns = {parcel_wrap.apn for parcel_wrap in parcel_wraps}
    missing_parcels = parcel_wrap_apns - parcel_apns
    missing_parcel_wraps = parcel_apns - parcel_wrap_apns
    print(f"# of parcels in Parcel but not ParcelWrap: {len(missing_parcel_wraps)}")
    print(f"# of parcels in ParcelWrap but not Parcel: {len(missing_parcels)}")
    if missing_parcel_wraps:
        print("Creating missing ParcelWrap entities...")
        new_parcel_wraps = [RawSfParcelWrap(apn=apn) for apn in missing_parcel_wraps]
        RawSfParcelWrap.objects.bulk_create(new_parcel_wraps, batch_size=500)
        for apn in missing_parcel_wraps:
            RawSfParcelWrap.objects.create(apn=apn)
        print("Done creating bare parcel wraps")
    if missing_parcels:
        print(
            "Note: Use viewer to resolve ParcelWraps without Parcel. Could mean some outdated parcel references"
            "  from docs like the housing element"
        )
    print("DONE checking completeness of parcel wrap entities")


def latest_instances(model: models.Model, apn_field) -> QuerySet:
    """Get the latest instances (latest run_date) of a model for each apn."""
    latest_run_dates = model.objects.filter(**{apn_field: OuterRef(apn_field)}).order_by("-run_date")[:1]

    # Main query to get the instances with the latest run_date for each apn
    latest_instances = model.objects.filter(id__in=Subquery(latest_run_dates.values("id")))

    return latest_instances


# Create missing links to ParcelWrap
...


def link_to_parcel_wrap_sf(model, apn_field, wrap_model_field):
    """Link the latest instances of a model to corresponding RawSfParcelWrap instance. Create RawSfParcelWrap
    if needed."""
    print(f"Checking links from {model.__name__} to RawSfParcelWrap...")
    # Get the latest instances of the model
    unlinked_rows = (
        latest_instances(model, apn_field)
        .annotate(num_fk_references=Count("rawsfparcelwrap"))
        .filter(num_fk_references=0)
    )
    missing_apns = {getattr(inst, apn_field) for inst in unlinked_rows}
    parcel_wraps = RawSfParcelWrap.objects.filter(apn__in=missing_apns)
    print(
        f"For model {model.__name__}, found {len(unlinked_rows)} latest unlinked APNs and {len(parcel_wraps)} "
        f"parcel wrap objects to link them to"
    )
    created_count = 0
    updated_wraps = []
    for idx, model_inst in enumerate(unlinked_rows):
        if idx % 1000 == 0:
            print(".", end="")
        apn = getattr(model_inst, apn_field)
        updated_wraps.append(RawSfParcelWrap(apn=apn, **{wrap_model_field: model_inst}))
    if len(updated_wraps):
        print("Writing updated links to DB...")
        # Update RawSfParcelWrap with the latest instances, or create if one with the correct APN doesn't exist yet.
        RawSfParcelWrap.objects.bulk_create(
            updated_wraps,
            batch_size=500,
            update_conflicts=True,
            unique_fields=["apn"],
            update_fields=[wrap_model_field],
        )
        print(
            f"Done adding links for model {model.__name__}. Updated or created {len(updated_wraps)} "
            f"RawSfParcelWrap objects"
        )
    else:
        print("DONE checking for unlinked APNs. No new links created")


def postprocess_sf():
    """After loading raw data, this method does post-processing like:
    - creating the RawSfParcelWrap model
    - any other checks and post-processing to be identified
    """
    check_for_dupes_sf()
    check_parcel_wraps_sf()
    # print("\nMatching APNs in RawSfParcel (blklot), RawSfHeTableA (mapblklot), and RawSfHeTableB(mapblklot)...")
    # parcel_apns = set(RawSfParcel.objects.values_list("blklot", flat=True))
    # table_a_apns = set(RawSfHeTableA.objects.values_list("mapblklot", flat=True))
    # table_b_apns = set(RawSfHeTableB.objects.values_list("mapblklot", flat=True))
    # print(f"Found {len(parcel_apns)} apns in RawSfParcel")
    # print(f"Found {len(table_a_apns)} apns in RawSfHeTableA")
    # print(f"Found {len(table_b_apns)} apns in RawSfHeTableB")

    link_to_parcel_wrap_sf(RawSfHeTableA, "mapblklot", "he_table_a")
    link_to_parcel_wrap_sf(RawSfHeTableB, "mapblklot", "he_table_b")
    link_to_parcel_wrap_sf(RawSfReportall, "parcel_id", "reportall_parcel")
