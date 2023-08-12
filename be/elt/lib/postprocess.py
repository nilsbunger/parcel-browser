from django.contrib.gis.db import models
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, OuterRef, QuerySet, Subquery
from django.forms import model_to_dict
from lib.util import flatten_dict, getattr_with_lookup_key
from parsnip.util import dict_del_keys

from elt.models import (
    RawGeomData,
    RawSfHeTableA,
    RawSfHeTableB,
    RawSfParcel,
    RawSfRentboardHousingInv,
    RawSfReportall,
)
from elt.models.raw_sf_parcel_wrap import RawSfParcelWrap


def filter_key(d, key_to_remove):
    return {k: v for k, v in d.items() if k != key_to_remove}


def check_for_dupes_raw_geom(dry_run: bool = False):
    """Look for duplicates in raw_geom"""
    # Annotate the locations with the count of identical geometries
    # Group by geometry and annotate the group with a list of IDs
    print("Looking for duplicates in RawGeomData...")
    locations_with_counts = (
        RawGeomData.objects.values("run_date", "geom", "juri", "data_type", "data", "rawsfparcelwrap_id")
        .annotate(identical_count=Count("id"), id_list=ArrayAgg("id"))
        .filter(identical_count__gt=1)
    )

    # Construct the duplicate groups from the aggregated data
    ids_to_delete = set({})
    for item in locations_with_counts:
        dup_rows = RawGeomData.objects.filter(id__in=item["id_list"]).values()
        duped_flat = [filter_key(flatten_dict(x), key_to_remove="id") for x in list(dup_rows)]
        all_same = all([duped_flat[0] == x for x in duped_flat])
        if not all_same:
            print("WEIRD")
        else:
            ids_to_delete = ids_to_delete | set(item["id_list"][1:])

    if not ids_to_delete:
        print("No duplicates found")
    elif not dry_run:
        print(f"Deleting {len(ids_to_delete)} rows")
        RawGeomData.objects.filter(id__in=ids_to_delete).delete()
    else:
        print(f"DRY RUN, would've deleted {len(ids_to_delete)} rows")
    print("Done with Raw Geom dupe check")


def check_for_dupes_sf(dry_run: bool = False):
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
                        if not dry_run:
                            model.objects.filter(pk=objs[i]["id"]).delete()
    if same_count > 0:
        print(("**DRY RUN** would've deleted" if dry_run else "Deleted") + f"{same_count} duplicates with same data")
    else:
        print("No duplicates found")


def check_parcel_wraps_sf(dry_run=False):
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
        if not dry_run:
            RawSfParcelWrap.objects.bulk_create(new_parcel_wraps, batch_size=500)
            print("Done creating bare parcel wraps")
        else:
            print(f"Would have created {len(missing_parcel_wraps)} bare parcel wraps")
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


def link_to_parcel_wrap_sf_many_to_one(model, apn_field, wrap_model_field, *, dry_run=False):
    """Link instances of a model to corresponding RawSfParcelWrap instance. Create RawSfParcelWrap
    if needed. This method is meant for models where there's a many-to-one relationship between the model and
    RawSfParcelWrap, with the foreign key in the model. There's no check for uniqueness here."""

    # Grab any instances of the model that don't have a link to a parcel wrap
    unlinked_rows = model.objects.filter(**{wrap_model_field: None})
    split_apn = apn_field.split("__")
    unlinked_apns = {getattr_with_lookup_key(inst, *split_apn) for inst in unlinked_rows}
    parcel_wraps = RawSfParcelWrap.objects.filter(apn__in=unlinked_apns)
    print(
        f"For model {model.__name__}, found {len(unlinked_rows)} unlinked entries (w/ {len(unlinked_apns)}"
        f" unique apn's), and {len(parcel_wraps)} parcel wrap objects to link them to"
    )
    parcel_wrap_by_apn_dict = {parcel_wrap.apn: parcel_wrap for parcel_wrap in parcel_wraps}
    print("Linking unlinked rows to parcel wraps...")
    updated_rows = []
    for idx, unlinked_row in enumerate(unlinked_rows):
        if idx % 500 == 0:
            print(".", end="")
        unlinked_row_apn = getattr_with_lookup_key(unlinked_row, *split_apn)
        if unlinked_row_apn in parcel_wrap_by_apn_dict:
            setattr(unlinked_row, wrap_model_field, parcel_wrap_by_apn_dict[unlinked_row_apn])
        else:
            print(f"Creating new parcel wrap for APN {unlinked_row_apn}")
            if not dry_run:
                parcel_wrap = RawSfParcelWrap.objects.create(apn=unlinked_row_apn)
                setattr(unlinked_row, wrap_model_field, parcel_wrap)
            else:
                print(f"DRY RUN: Would've linked {unlinked_row} to new parcel wrap for apn={unlinked_row_apn}")
            unlinked_row.save(update_fields=[wrap_model_field])
        updated_rows.append(unlinked_row)

    if not dry_run and updated_rows:
        print("\nSaving updated rows...")
        model.objects.bulk_create(
            updated_rows,
            batch_size=500,
            update_conflicts=True,
            unique_fields=["id"],
            update_fields=[wrap_model_field],
        )
        print("Done saving updated rows")
    elif not updated_rows:
        print("No rows to save")
    else:
        print(f"DRY RUN: Would have saved {len(updated_rows)} rows to parcel wraps")


def link_to_parcel_wrap_sf_one_to_one(model, apn_field, wrap_model_field, dry_run=False):
    """Link the latest instances of a model to corresponding RawSfParcelWrap instance. Create RawSfParcelWrap
    if needed.

    This method makes two assumptions about the model:
     * there's a one-to-one relationship between the model and RawSfParcelWrap w/ foreign key in RawSfParcelWrap.
     * run_date,apn is unique for the model.
    """
    print(f"Checking links from {model.__name__} to RawSfParcelWrap...")
    # Get the latest instances of the model where it isn't linked from a parcel wrap foreign key.
    unlinked_rows = (
        latest_instances(model, apn_field)
        .annotate(num_fk_references=Count("rawsfparcelwrap"))  # Count uses related model's foreign key.
        .filter(num_fk_references=0)
    )
    unlinked_apns = {getattr(inst, apn_field) for inst in unlinked_rows}
    parcel_wraps = RawSfParcelWrap.objects.filter(apn__in=unlinked_apns)
    print(
        f"For model {model.__name__}, found {len(unlinked_rows)} latest unlinked APNs and {len(parcel_wraps)} "
        f"parcel wrap objects to link them to"
    )
    updated_wraps = []
    for idx, model_inst in enumerate(unlinked_rows):
        if idx % 1000 == 0:
            print(".", end="")
        apn = getattr(model_inst, apn_field)
        updated_wraps.append(RawSfParcelWrap(apn=apn, **{wrap_model_field: model_inst}))
    if len(updated_wraps):
        if not dry_run:
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
                f"\nDone adding links for model {model.__name__}. Updated or created {len(updated_wraps)} "
                f"RawSfParcelWrap objects"
            )
        else:
            print(
                f"\nDRY RUN: Would've added {len(updated_wraps)} links for model {model.__name__} to "
                f"RawSfParcelWrap objects"
            )
    else:
        print("DONE checking for unlinked APNs. No new links created")


def postprocess_sf(*, dry_run=False):
    """After loading raw data, this method does post-processing like:
    - creating the RawSfParcelWrap model
    - any other checks and post-processing to be identified
    """
    check_for_dupes_raw_geom(dry_run=dry_run)
    check_for_dupes_sf(dry_run=dry_run)
    check_parcel_wraps_sf(dry_run=dry_run)
    # print("\nMatching APNs in RawSfParcel (blklot), RawSfHeTableA (mapblklot), and RawSfHeTableB(mapblklot)...")
    # parcel_apns = set(RawSfParcel.objects.values_list("blklot", flat=True))
    # table_a_apns = set(RawSfHeTableA.objects.values_list("mapblklot", flat=True))
    # table_b_apns = set(RawSfHeTableB.objects.values_list("mapblklot", flat=True))
    # print(f"Found {len(parcel_apns)} apns in RawSfParcel")
    # print(f"Found {len(table_a_apns)} apns in RawSfHeTableA")
    # print(f"Found {len(table_b_apns)} apns in RawSfHeTableB")

    link_to_parcel_wrap_sf_many_to_one(
        RawSfRentboardHousingInv, "parcel_number", wrap_model_field="rawsfparcelwrap", dry_run=dry_run
    )
    link_to_parcel_wrap_sf_many_to_one(
        RawGeomData, "data__mapblklot", wrap_model_field="rawsfparcelwrap", dry_run=dry_run
    )
    link_to_parcel_wrap_sf_one_to_one(RawSfParcel, "blklot", wrap_model_field="parcel", dry_run=dry_run)
    link_to_parcel_wrap_sf_one_to_one(RawSfHeTableA, "mapblklot", wrap_model_field="he_table_a", dry_run=dry_run)
    link_to_parcel_wrap_sf_one_to_one(RawSfHeTableB, "mapblklot", wrap_model_field="he_table_b", dry_run=dry_run)
    link_to_parcel_wrap_sf_one_to_one(
        RawSfReportall, "parcel_id", wrap_model_field="reportall_parcel", dry_run=dry_run
    )
