from datetime import datetime
from zoneinfo import ZoneInfo

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
    parcels_by_faith_owners = RawSfParcelWrap.objects.filter(reportall_parcel__owner__in=faith_owners)
    print(f"Found {len(faith_parcels)} parcels with land_use_code=Churches,Convents,Rectories")
    print(f"Found {len(faith_owners)} unique owners")
    print(f"Found {len(parcels_by_faith_owners)} parcels owned by orgs with another faith parcel")

    old_results = EltAnalysis.objects.filter(juri=geo.value, analysis=EltAnalysisEnum.yigby.value)
    if old_results:
        print(f"Found {len(old_results)} previous results, deleting them...")
    else:
        print("... no previous results found.")
    for res in old_results:
        print(f"... Result had {res.parcels.count()} parcel relationships")
    old_results.delete()
    e = EltAnalysis(
        juri=geo.value,
        analysis=EltAnalysisEnum.yigby.value,
        run_date=datetime.now(tz=ZoneInfo("America/Los_Angeles")).date(),
    )
    e.save()
    e.parcels.set(parcels_by_faith_owners)
    print(f"Created EltAnalysis with {len(parcels_by_faith_owners)} related parcels.")
