import sys
from dataclasses import dataclass
from pathlib import Path

# import fixtures from zip file since they get so big
sys.path.insert(0, str(Path(__file__).resolve().parent / "attom_90006_apts.py.zip"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "attom_comps_2769_san_marino_90006.py.zip"))
# noinspection PyUnresolvedReferences
import attom_90006_apts  # noqa: E402 - import not at top of file

# noinspection PyUnresolvedReferences
import attom_comps_2769_san_marino_90006  # noqa: E402 - import not at top of file


# /property/address: get units in a zip code. zip=90006, apartments with more than 12 bedrooms (2 pages of results)
@dataclass(frozen=True)
class AttomPropertyAddressFixture:
    APTS_90006_PG1 = attom_90006_apts.props_90006_apartments_pg1
    APTS_90006_PG2 = attom_90006_apts.props_90006_apartments_pg2


@dataclass(frozen=True)
class AttomCompsFixture:
    COMPS_2769_SAN_MARINO = attom_comps_2769_san_marino_90006.comps_2769_san_marino_90006
