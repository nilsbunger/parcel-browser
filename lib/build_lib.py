from pydantic import BaseModel

from lib.finance_lib import Financials
from lib.re_params import BuildableUnit


class DevScenario(BaseModel):
    adu_qty: int
    unit_type: BuildableUnit
    finances: Financials
