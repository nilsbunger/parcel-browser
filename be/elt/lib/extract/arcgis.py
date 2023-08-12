import json
import traceback
from copy import deepcopy

import requests

from elt.lib.elt_utils import get_elt_file_assets, log_and_print, pipestage_prompt
from elt.lib.types import GisData, Juri
from elt.models import RawSantaAnaParcel


# Extract data from an ArcGIS server with API calls. Support different cities and data types (parcels, zones, etc).
# pipestage is defined in the ARCGIS_DATA_SOURCES dict. thru_data is data passed from previous stages into the
# fetcher. This function writes the results of each stage to a file, can reuse previous fetches, and logs the
# capture. The function returns the filename in which the data was written.
def extract_from_arcgis_api(geo: Juri, datatype: GisData, pipestage: int, thru_data=None):
    from elt.lib.extract.params import ARCGIS_DATA_SOURCES, DATA_DIR

    stage_config = ARCGIS_DATA_SOURCES[geo][datatype][pipestage]
    geo_name = ARCGIS_DATA_SOURCES[geo]["geo_name"]
    print(f"Extract from Arc GIS API pipe stage: geo={geo}, datatype={datatype}, {pipestage}: {stage_config['name']}")
    if stage_config["has_file_output"]:  # file-based output
        pipestage_dirname = f"{pipestage}.{stage_config['name']}"
        file_assets = get_elt_file_assets(geo, datatype, pipestage_dirname, extension="jsonl")
        existing_files = file_assets.latest_files
        resolved_datatype = file_assets.resolved_datatype
        new_filesname = file_assets.new_filename
    else:
        existing_files, new_filename = [], "DB"  # noqa: F841 unused variable

    if stage_config["has_file_output"] and not existing_files:
        print("No existing file found... Creating one.")
        use_file = "c"
        existing_filename = "NONE"
    else:
        # Prompt user for intention - either there are existing output files or it's a DB-based output
        existing_filename = existing_files[0].name if stage_config["has_file_output"] else "DB"
        use_file = pipestage_prompt(
            is_incremental=stage_config["is_incremental"],
            existing_filename=existing_filename,
        )

    # Got user intention, either fetch new data (create_new_file), incrementally add to latest file (do_incremental),
    # or load existing data
    if use_file == "c":  # create new data
        outfile = new_filesname
        logmsg = f"Fetched {geo_name} {resolved_datatype} {stage_config['name']}, wrote to {outfile}\n"
    elif use_file == "i":  # incrementally add to latest file
        outfile = existing_filename
        logmsg = f"Fetched {geo_name} {resolved_datatype} {stage_config['name']}, wrote incrementally to {outfile}\n"
    elif use_file == "s":  # skip stage, using existing data
        outfile = existing_filename
        logmsg = (
            f"Skip stage, with existing {geo_name} {resolved_datatype} {stage_config['name']} data from {outfile}\n"
        )
    else:
        raise NotImplementedError("Not implemented yet - use older existing data")

    # Fetch data from API or from file
    file_to_write = (new_filesname if use_file == "c" else outfile,)
    result_count = stage_config["fetcher_fn"](
        stage_config["url"],
        stage_config["custom_params"],
        outfile=file_to_write,
        thru_data=thru_data,
        do_incremental=(use_file == "i"),
        skip_stage=(use_file == "s"),
    )
    with open(DATA_DIR / "elt-fetches.log", "a") as log:
        log_and_print(f"{logmsg}        Extracted {result_count} objects.\n", log)
    return outfile


# Execute one query to Arc GIS server and process its response. Apply default parameters, and merge with query-specific
# parameters. Return the response as a JSON object.
def arc_gis_get(url, arc_custom_params):
    from elt.lib.extract.params import DEFAULT_ARCGIS_PARAMS

    params = deepcopy(DEFAULT_ARCGIS_PARAMS)
    params.update(arc_custom_params)
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(
            f"Error getting data from GIS server:\n {response.status_code}\n {response.reason}\n{response.content}"
        )
    if params["f"] in ["pjson", "geojson"]:
        result = response.json()
        if result.get("error"):
            raise Exception(f"Error getting data from GIS server:\n {result}")
        # TODO: need to catch errors here that return as status_code 200
        return result
    else:
        raise Exception(f"Unsupported format: {params['f']}")


# Support fn: Fetch object IDs from an ArcGIS server and save them to a file. Return the objects for processing
def object_id_fetcher(url, arc_custom_params, *, outfile, skip_stage=False):
    if skip_stage:
        with open(outfile) as f:
            data = json.load(f)
        assert list(data.keys()) == ["objectIdFieldName", "objectIds"]
        return len(data["objectIds"])

    data = arc_gis_get(url, arc_custom_params)
    assert list(data.keys()) == ["objectIdFieldName", "objectIds"]
    with open(outfile, "w") as f:
        json.dump(data, f)  # note: this writes a JSONL file but with only one line.
    return len(data["objectIds"])


# Fetch parcels specified by object IDs and write or append the results  into the database.
# This does multiple batched calls to the ArcGIS server. Returns the number of items fetched.
def parcel_data_fetcher(url, arc_custom_params, *, do_incremental, thru_data, skip_stage=False):
    # If we are using existing data, no fetching, just return how many entries exist.
    if skip_stage:
        count = RawSantaAnaParcel.objects.all().count()
        return count
    count = 0
    error_count = 0
    parcels = []
    fields = [field.name for field in RawSantaAnaParcel._meta.get_fields() if not field.primary_key]

    # Get all Object IDs found by querying Arc GIS server in previous stage.
    with open(thru_data["object_id_file"]) as f:
        data = json.load(f)
    object_ids_in_dataset = set(data["objectIds"])

    # Figure out which Object IDs to fetch (if incremental, don't refetch ones we already have)
    fetched_object_ids = set()
    if do_incremental:
        # incremental means we reuse previously stored objects where they exist. Object IDs aren't always stable,
        # so sometimes we will refetch parcels we already have anyway. But c'est la vie.
        fetched_object_ids = set(RawSantaAnaParcel.objects.values_list("object_id", flat=True))

    pending_object_ids = list(object_ids_in_dataset - fetched_object_ids)
    print(
        f"Need to fetch {len(pending_object_ids)} parcels out of {len(object_ids_in_dataset)} parcels "
        f"in the server's dataset. Previously had {len(fetched_object_ids)} in DB."
    )

    gis_fetch_batch_size = 50  # if it's too high, ArcGIS refuses to respond
    # Fetch all the parcels indicated by pending_object_ids, in batches.
    while pending_object_ids:
        # fetch a batch of parcels using a list of object IDs
        objs_to_fetch_this_batch = pending_object_ids[:gis_fetch_batch_size]
        arc_custom_params["objectIds"] = ",".join([str(x) for x in objs_to_fetch_this_batch])
        pending_object_ids = pending_object_ids[gis_fetch_batch_size:]

        data = arc_gis_get(url, arc_custom_params)

        if len(data["features"]) < len(objs_to_fetch_this_batch):
            print(
                f"WARNING: fewer parcels returned than requested. Got {len(data['features'])} objects. "
                f"Stale object IDs? Aborting..."
            )
            return count
        # now write the batch of parcels to the database (breaking into chunks of 50)
        for parcel_data in data["features"]:
            count += 1
            try:
                p = RawSantaAnaParcel.create(parcel_data)
                p.clean_fields()  # can't do "full_clean" here, it seems to check against DB's uniqueness constraint
                p.clean()
                parcels.append(p)
            except Exception as e:
                print(f"Error creating parcel object: {e}")
                traceback.print_exc()
                # Allow us to continue and try with more parcels
                error_count += 1
            if count % 50 == 0:
                print(f"Writing batch of {len(parcels)} parcels to DB (total so far: {count})")
                try:
                    RawSantaAnaParcel.objects.bulk_create(
                        parcels,
                        update_conflicts=True,
                        update_fields=fields,
                        unique_fields=["assessment_no", "legal_lot_id", "name"],
                        batch_size=50,
                    )
                except Exception as e:
                    print(f"Error writing batch of parcels to DB: {e}")
                    traceback.print_exc()
                    error_count += 1
                    # Allow us to continue and try with more batches.
                parcels = []
    # If the last batch is not a full batch, write it now.
    if parcels:
        RawSantaAnaParcel.objects.bulk_create(
            parcels,
            update_conflicts=True,
            update_fields=fields,
            unique_fields=["assessment_no", "legal_lot_id", "name"],
            batch_size=50,
        )
        parcels = []  # noqa: F841 unused variable
    print(f"DONE writing parcels to DB. Wrote {count} parcels. {error_count} errors.")
    return count
