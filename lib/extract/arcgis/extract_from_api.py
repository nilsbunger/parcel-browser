from copy import deepcopy
from datetime import datetime
import json
import traceback
from zoneinfo import ZoneInfo

import requests
from rich.prompt import Prompt

from elt.models import RawSantaAnaParcel
from lib.extract.arcgis.types import GeoEnum, GisDataTypeEnum


# Execute one query to Arc GIS server and process its response. Apply default parameters, and merge with query-specific
# parameters. Return the response as a JSON object.
def arc_gis_get(url, arc_custom_params):
    from lib.extract.arcgis.params import ARCGIS_DATA_SOURCES, DATA_DIR, DEFAULT_ARCGIS_PARAMS

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


# Fetch object IDs from an ArcGIS server and save them to a file. Return the objects for processing
def object_id_fetcher(url, arc_custom_params, outfile, do_incremental, thru_data, use_existing_data=False):
    if use_existing_data:
        with open(outfile) as f:
            data = json.load(f)
        assert list(data.keys()) == ["objectIdFieldName", "objectIds"]
    else:
        data = arc_gis_get(url, arc_custom_params)
        with open(outfile, "w") as f:
            json.dump(data, f)  # note: this writes a JSONL file but with only one line.
    num_results = len(data["objectIds"])
    return num_results


# Fetch parcels specified by object IDs and write or append the results  into the database.
# This does multiple batched calls to the ArcGIS server. Returns the number of items fetched.
def parcel_data_fetcher(url, arc_custom_params, outfile, do_incremental, thru_data, use_existing_data=False):
    # "objectIds": ",".join([str(x) for x in object_ids["objectIds"]]),

    # If we are using existing data, no fetching, just return how many entries exist.
    count = 0
    parcels = []
    fields = [field.name for field in RawSantaAnaParcel._meta.get_fields() if not field.primary_key]
    if use_existing_data:
        count = RawSantaAnaParcel.objects.all().count()
        return count

    # Get all Object IDs found by querying Arc GIS server in previous stage.
    with open(thru_data["object_id_file"]) as f:
        data = json.load(f)
    object_ids_in_dataset = set(data["objectIds"])

    # Figure out which Object IDs to fetch (if incremental, don't refetch ones we already have)
    fetched_object_ids = set()
    if do_incremental:
        # incremental means we reuse previously captured object IDs. Object IDs aren't always stable, so sometimes
        # we will refetch parcels we already have. But c'est la vie.
        fetched_object_ids = set(RawSantaAnaParcel.objects.values_list("object_id", flat=True))
        # TODO: figure out which object IDs are already captured, and populate fetched_object_ids with them.
    pending_object_ids = list(object_ids_in_dataset - fetched_object_ids)
    print(
        f"Need to fetch {len(pending_object_ids)} parcels out of {len(object_ids_in_dataset)} parcels "
        f"in the server's dataset. Previously had {len(fetched_object_ids)} in DB."
    )

    # control batch size of arc gis fetches here... if it's too high, the ArcGIS server rejects the request
    batch_size = 50

    # Fetch all the parcels indicated by pending_object_ids, in batches.
    while pending_object_ids:
        # fetch a batch of parcels using a list of object IDs
        objs_to_fetch_this_batch = pending_object_ids[:batch_size]
        arc_custom_params["objectIds"] = ",".join([str(x) for x in objs_to_fetch_this_batch])
        pending_object_ids = pending_object_ids[batch_size:]
        data = arc_gis_get(url, arc_custom_params)
        if len(data["features"]) < len(objs_to_fetch_this_batch):
            print(
                f"WARNING: fewer parcels returned than requested. Got {len(data['features'])} objects. "
                f"Stale object IDs? Aborting..."
            )
            return count
        error_count = 0
        # now write the batch of parcels to the database (breaking into chunks of 50)
        for parcel_data in data["features"]:
            count += 1
            try:
                p = RawSantaAnaParcel.create(parcel_data)
                p.clean_fields()  # can't do "full_clean" here, it seems to check against DB's uniqueness constraint
                p.clean()
            except Exception as e:
                print(f"Error creating parcel object: {e}")
                traceback.print_exc()
                # Allow us to continue and try with more parcels
                error_count += 1.0
            parcels.append(p)
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
                    traceback.print_exception()
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
