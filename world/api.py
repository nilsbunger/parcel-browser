import tempfile
import traceback

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.gis.db.models.functions import Centroid
from django.db.models import F
from ninja import NinjaAPI, Query
from ninja.pagination import paginate
from ninja.security import django_auth

from lib.parcel_analysis_2022.analyze_parcel_lib import analyze_one_parcel
from lib.co.co_eligibility_lib import AB2011Eligible
from lib.parcel_analysis_2022.crs_lib import get_utm_crs
from lib.parcel_analysis_2022.listings_lib import address_to_parcel
from mygeo.util import field_exists_on_model
from world.api_gis_schema import (
    AnalysisResponseSchema,
    ListingHistorySchema,
    ListingSchema,
    ListingsFilters,
    ParcelSchema,
    RentalRatesSchema,
    RoadSchema,
)
from world.models import AnalyzedListing, Parcel, PropertyListing, RentalData, Roads

# Require auth on all API routes (can be overriden if needed)
world_api = NinjaAPI(auth=django_auth, csrf=True, urls_namespace="world_api", docs_decorator=staff_member_required)

################################################################################################
## GIS APIs
################################################################################################


@world_api.get("/world/listinghistory", response=list[ListingHistorySchema])
def get_listing_history(request, mlsid: str):
    listings = PropertyListing.objects.filter(mlsid=mlsid).order_by("-founddate")
    return listings


@world_api.get("/world/rentalrates")  # response=List[RentalRatesSchema])
def get_rental_rates(request) -> list[RentalRatesSchema]:
    rental_data = RentalData.objects.exclude(details__has_key="status_code").order_by("parcel", "-details__mean")
    pid: str = ""
    retlist = []
    for rd in rental_data:
        if rd.parcel_id != pid:
            retlist.append(
                {
                    "pid": rd.parcel_id,
                    "lat": round(rd.location.y, 7),
                    "long": round(rd.location.x, 7),
                    "rents": {},
                }
            )
        assert retlist[-1]["pid"] == rd.parcel_id
        retlist[-1]["rents"][f"{rd.br}BR,{rd.ba}BA"] = {
            "rent_mean": rd.details["mean"],
            "rent_75_percentile": rd.details["percentile_75"],
            "num_samples": rd.details["samples"],
        }
        pid = rd.parcel_id

    # print(f"Returning {len(retlist)} items")
    # pprint.pprint(retlist)
    return retlist


@world_api.get("/world/listings", response=list[ListingSchema])
@paginate
def get_listings(request, order_by: str = "founddate", asc: bool = False, filters: ListingsFilters = Query(...)):
    # Strip away the filter params that are none
    # Filters are already validated by the ListingsFilters Schema above
    filters_xlat = {
        "is_mf": "analyzedlisting__is_mf",
        "is_tpa": "analyzedlisting__is_tpa",
        "neighborhood__contains": "neighborhood__in",
    }

    # TODO : Next line is a hack - we're sending neighborhood list as comma-separated string instead of array
    if filters.neighborhood__contains is not None:
        filters.neighborhood__contains = filters.neighborhood__contains[0].split(",")

    filter_params = {}
    for key in filters.dict():
        if filters.dict()[key] is not None:
            if key in ["is_mf", "is_tpa"] and filters.dict()[key] is False:
                # is_mf, or is_mf mean "only mf / only tpa". so if it's false, don't add a filter criteria
                continue
            filter_params[filters_xlat.get(key, key)] = filters.dict()[key]

    # Construct ordering query: if the field doesn't exist on the PropertyListing model, it probably exists
    # either on AnalyzedListing model or AnalyzedListing's detail field, so let's prefix it
    if not field_exists_on_model(PropertyListing, order_by):
        if field_exists_on_model(AnalyzedListing, order_by):
            # field is on AnalyzedListing.
            order_by = "analyzedlisting__" + order_by
        else:
            order_by = "analyzedlisting__details__" + order_by

    if not asc:
        order_by = "-" + order_by

    listings = (
        PropertyListing.active_listings_queryset()
        .filter(analyzedlisting__isnull=False, **filter_params)
        .prefetch_related("analyzedlisting", "prev_listing", "parcel")
        .annotate(centroid=Centroid(F("parcel__geom")))
        .order_by(order_by)
    )

    return listings


@world_api.post("/world/analysis/")
def redo_analysis(request, apn: str = None, al_id: int = None):
    """Trigger a re-run of parcel analysis, used by /new-listing frontend"""

    if al_id:
        analyzed_listing = AnalyzedListing.objects.prefetch_related("listing").get(id=al_id)
        property_listing = analyzed_listing.listing
    else:
        parcel = Parcel.objects.get(apn=apn)
        property_listing = PropertyListing.get_latest_or_create(parcel)

    sd_utm_crs = get_utm_crs()  # San Diego specific

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Generally should match this call to analyze_batch() call in scrape.py
        analyzed_listing = analyze_one_parcel(
            property_listing.parcel,
            sd_utm_crs,
            property_listing,
            save_dir=tmpdirname,
            dry_run=False,
            show_plot=False,
            force_uploads=True,
        )

    return {"analysisId": analyzed_listing.id}


@world_api.get("/world/analysis/{al_id}", response=AnalysisResponseSchema)
def get_analysis(request, al_id: int):
    """Get analysis results for a given analysis id"""
    # al_json = AnalysisResponseSchema.from_orm(analyzed_listing).dict()
    return AnalyzedListing.objects.prefetch_related("listing").get(id=al_id)


@world_api.get("/world/parcel/{apn}", response=ParcelSchema)
def get_parcel(request, apn: str):
    """Get parcel info for a given APN"""
    parcel = Parcel.objects.get(apn=apn)
    x = AB2011Eligible()
    x.run(parcel)
    retval = ParcelSchema.from_orm(parcel)
    retval.ab2011_result = x.check
    return retval


@world_api.get("/world/road/{road_segid}", response=RoadSchema)
def get_road(request, road_segid: int):
    """Get road info for a given road segid"""
    return Roads.objects.get(roadsegid=road_segid)


@world_api.get("/world/address-search/{addr}")
def address_search(request, addr: str):
    """Look up an address and return a parcel if there's a single match."""
    # Takes in an address. Returns a list of possible parcels/APNs
    # Temporary. Let's clean this up later
    try:
        parcel, error = address_to_parcel(addr, jurisdiction="SD")
        # TODO: Finish this better address matcher
        # parcel, error = address_to_parcels_loose(addr)
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
    if error:
        return {"error": f"An error occurred: {error}"}
    try:
        analyzed_listing = AnalyzedListing.objects.filter(parcel=parcel).order_by("-datetime_ran")[0]
    except IndexError:
        analyzed_listing = None
    except Exception as e:
        traceback.print_exc()
        return {"error": "AnalyzedListing lookup failed:" + str(e)}

    analysis_id = analyzed_listing.id if analyzed_listing else None
    return {"apn": parcel.apn, "address": parcel.address, "analyzed_listing": analysis_id}
