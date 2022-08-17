from collections import OrderedDict

from pydantic import BaseModel


class FinanceCategory(BaseModel):
    cat_name: str
    costs: list[list[str, int]]


class Financials(BaseModel):
    capital_flow: OrderedDict[str, list[tuple[str, int, str]]] = OrderedDict()
    operating_flow: list[tuple[str, int, str]] = []

    def dict(self, *args, **kwargs):
        x = super().dict(*args, **kwargs)
        x['capital_sum'] = self.capital_sum_calc
        x['net_income'] = self.net_income_calc
        x['cap_rate'] = self.cap_rate_calc
        return x

    @property
    def net_income_calc(self):
        return round(sum([x[1] for x in self.operating_flow]))

    @property
    def capital_sum_calc(self):
        # Flatten ordered dictionary to just get dollar amounts.
        return round(sum([el[1] for item in self.capital_flow.items() for el in item[1]]))

    @property
    def cap_rate_calc(self):
        if self.capital_sum_calc == 0:
            return 0
        else:
            return round((self.net_income_calc * 12) / (0 - self.capital_sum_calc) * 100, 2)
