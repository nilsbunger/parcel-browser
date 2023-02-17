from copy import deepcopy
from datetime import datetime
import json
import traceback
from zoneinfo import ZoneInfo

import requests
from rich.prompt import Prompt

from elt.models import RawSantaAnaParcel
from lib.extract.arcgis.types import GeoEnum, GisDataTypeEnum
from lib.extract.elt_utils import get_elt_pipe_filenames, log_and_print, pipestage_prompt


# Extract data from an ArcGIS server with API calls. Support different cities and data types (parcels, zones, etc).
# pipestage is defined in the ARCGIS_DATA_SOURCES dict. thru_data is data passed from previous stages into the
# fetcher. This function writes the results of each stage to a file, can reuse previous fetches, and logs the
# capture. The function returns the filename in which the data was written.
def extract_from_arcgis_api(geo: GeoEnum, datatype: GisDataTypeEnum, pipestage: int, thru_data=None):
    from lib.extract.arcgis.params import ARCGIS_DATA_SOURCES, DATA_DIR

    stage_config = ARCGIS_DATA_SOURCES[geo][datatype][pipestage]
    geo_name = ARCGIS_DATA_SOURCES[geo]["geo_name"]
    print(
        f"Extract from Arc GIS API pipe stage: geo={geo}, datatype={datatype}, {pipestage}: {stage_config['name']}"
    )
    if stage_config["has_file_output"]:  # file-based output
        pipestage_dirname = f"{pipestage}.{stage_config['name']}"
        existing_files, new_file = get_elt_pipe_filenames(geo, datatype, pipestage_dirname)
    else:
        existing_files, new_file = [], "DB"

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
        outfile = new_file
        logmsg = f"Fetched {geo_name} {datatype} {stage_config['name']}, wrote to {outfile}\n"
    elif use_file == "i":  # incrementally add to latest file
        outfile = existing_filename
        logmsg = f"Fetched {geo_name} {datatype} {stage_config['name']}, wrote incrementally to {outfile}\n"
    elif use_file == "s":  # skip stage, using existing data
        outfile = existing_filename
        logmsg = f"Skip stage, with existing {geo_name} {datatype} {stage_config['name']} data from {outfile}\n"
    else:
        raise NotImplementedError("Not implemented yet - use older existing data")

    # Fetch data from API or from file
    result_count = stage_config["fetcher_fn"](
        stage_config["url"],
        stage_config["custom_params"],
        outfile=new_file if use_file == "c" else outfile,
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
    from lib.extract.arcgis.params import DEFAULT_ARCGIS_PARAMS

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
                error_count += 1.0
            if count % 50 == 0:
                print(f"Writing batch of 50 parcels to DB (total so far: {count})")
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
        parcels = []
    print(f"DONE writing parcels to DB. Wrote {count} parcels. {error_count} errors.")
    return count


# Extract data from an ArcGIS server with API calls. Support different cities and data types (parcels, zones, etc).
# pipestage is defined in the ARCGIS_DATA_SOURCES dict. thru_data is data passed from previous stages into the
# fetcher. This function writes the results of each stage to a file, can reuse previous fetches, and logs the
# capture. The function returns the filename in which the data was written.
def extract_from_arcgis_api(
    geo: GeoEnum, datatype: GisDataTypeEnum, pipestage: int, thru_data=None, always_use_existing=False
):
    _____url = (
        "https://www.ocgis.com/survey/rest/services/WebApps/ParcelFeatures/FeatureServer/0/query?"
        "where=SiteAddress+LIKE+%27%25santa+ana%27&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&"
        "inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=&"
        "returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion="
        "&historicMoment=&returnDistinctValues=false&returnIdsOnly=true&returnCountOnly=false&returnExtentOnly=false"
        "&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false"
        "&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false"
        "&returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false"
        "&timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault"
        "&datumTransformation=&f=pjson"
    )
    from lib.extract.arcgis.params import ARCGIS_DATA_SOURCES, DATA_DIR

    stage_config = ARCGIS_DATA_SOURCES[geo][datatype][pipestage]
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    pipe = ARCGIS_DATA_SOURCES[geo][datatype][pipestage]
    geo_name = ARCGIS_DATA_SOURCES[geo]["geo_name"]
    output_dir = DATA_DIR / geo.value / "shapes" / datatype.value / f"{pipestage}.{stage_config['name']}"
    logfile = DATA_DIR / "elt-fetches.log"
    log = open(logfile, "a")
    assert output_dir.is_dir()
    print(f"Pipe stage {pipestage}: {stage_config['name']}")

    # Check if we have previously stored data for this pipestage. If so, ask user whether to re-use or fetch new data.
    existing_files = sorted(output_dir.iterdir(), reverse=True)
    if not existing_files:
        print("No existing file found... Creating one.")
        create_new_file = True
        do_incremental = False
        use_file = -1
    else:
        print("Found files:")
        for i, f in enumerate(existing_files):
            print(f"{i + 1}: {f.name}")
        print(f"{len(existing_files) + 1}:Create new file")
        prompt_options = [str(x[0]) for x in enumerate(existing_files, start=1)] + [str(len(existing_files) + 1)]
        do_incremental = stage_config[
            "is_incremental"
        ]  # default to incremental if possible, overridden by user prompt
        if stage_config["is_incremental"]:
            print(f"{len(existing_files) + 2}:Incrementally add to latest file ({existing_files[0].name})")
            prompt_options += [str(len(existing_files) + 2)]
        if always_use_existing:
            print("Using latest file (always_use_existing=True)")
            create_new_file = False
            use_file = 1
        else:
            use_file = int(Prompt.ask("Which file to use?", choices=prompt_options))
            do_incremental = use_file == len(existing_files) + 2
            create_new_file = use_file == len(existing_files) + 1

    # Got user intention, either fetch new data, incrementally add to latest file, or load existing data
    if create_new_file:
        outfile = output_dir / f"{now.strftime('%y%m%d')}.jsonl"
        logmsg = f"Fetched {geo_name} {datatype} {stage_config['name']}, wrote to:\n        {outfile}\n"
    elif do_incremental:
        outfile = existing_files[0]
        logmsg = (
            f"Fetched {geo_name} {datatype} {stage_config['name']}, wrote incrementally to:\n        {outfile}\n"
        )
    else:  # load existing data file (outfile is really "input file" in this case)
        outfile = existing_files[use_file - 1]
        logmsg = f"Using existing {geo_name} {datatype} {stage_config['name']} file:\n        {outfile}\n"

    # Fetch data from API or from file
    result_count = stage_config["fetcher_fn"](
        stage_config["url"],
        stage_config["custom_params"],
        outfile,
        do_incremental,
        thru_data=thru_data,
        use_existing_data=not create_new_file and not do_incremental,
    )

    logmsg = f"{now.strftime('%y%m%d %H:%M:%S')} :: {logmsg}        Extracted {result_count} objects.\n"
    log.write(logmsg)
    log.close()
    print(logmsg)
    # rich.print_json(data=data)
    return outfile
