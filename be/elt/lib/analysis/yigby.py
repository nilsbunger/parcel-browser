from datetime import datetime
from zoneinfo import ZoneInfo

from elt.lib.standardize import ParcelFacts, create_parcel_facts_csv
from elt.lib.types import EltAnalysisEnum, Juri
from elt.models import RawSfParcelWrap
from elt.models.elt_analysis import EltAnalysis


def analyze_yigby(geo: Juri):
    print(f"Analyzing YIGBY for {geo.name} ")
    assert geo == Juri.sf
    faith_parcels = RawSfParcelWrap.objects.filter(
        reportall_parcel__land_use_class="Churches,Convents,Rectories"
    ).select_related("reportall_parcel")
    faith_owners = {x.reportall_parcel.owner for x in faith_parcels}
    faith_parcels_qs = (
        RawSfParcelWrap.objects.filter(reportall_parcel__owner__in=faith_owners)
        .select_related("parcel", "reportall_parcel", "he_table_a", "he_table_b")
        .prefetch_related("rawsfrentboardhousinginv_set")
        .prefetch_related("rawgeomdata_set")
    )

    print(f"Found {len(faith_parcels)} parcels with land_use_code=Churches,Convents,Rectories")
    print(f"Found {len(faith_owners)} unique owners")
    print(f"Found {faith_parcels_qs.count()} parcels owned by these faith owners")

    print(f"Creating sf_yigby.csv with {faith_parcels_qs.count()} parcels")
    facts: list[ParcelFacts] = []
    for _idx, obj in enumerate(faith_parcels_qs.iterator(chunk_size=2000)):
        facts.append(ParcelFacts.from_orm(obj))

    create_parcel_facts_csv(facts, "sf_yigby.csv")

    old_results = EltAnalysis.objects.filter(juri=geo.value, analysis=EltAnalysisEnum.yigby.value)
    if old_results:
        print(f"Found {len(old_results)} previous EltAnalysis map results, deleting them...")
    else:
        print("... no previous results found.")
    for res in old_results:
        print(f"... Result had {res.parcels.count()} parcel relationships")

    # Create ELT analysis that maps potential YIGBY parcels
    old_results.delete()  # this deletes the ELT analysis and related many-to-many table
    e = EltAnalysis(
        juri=geo.value,
        analysis=EltAnalysisEnum.yigby.value,
        run_date=datetime.now(tz=ZoneInfo("America/Los_Angeles")).date(),
    )
    e.save()
    # set many-to-many field (includes saving to DB)
    e.parcels.set(faith_parcels_qs)

    print(f"Created EltAnalysis with {faith_parcels_qs.count()} related parcels.")
