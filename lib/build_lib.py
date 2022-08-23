from pprint import pformat

from pydantic import BaseModel

from lib.finance_lib import Financials
from lib.re_params import BuildableUnit


class DevScenario(BaseModel):
    adu_qty: int
    unit_type: BuildableUnit
    finances: Financials

    def __repr__(self):
        return pformat({'adu_qty': self.adu_qty, 'unit_type': self.unit_type})
