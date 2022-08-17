from typing import List

from pydantic import BaseModel

from world.models.base_models import RentalUnit


class ConstructionCosts(BaseModel):
    # soft costs: $/sqft of new construction. Ref: https://snapadu.com/blog/all-about-adu-fees-waivers/
    soft_cost_rate: float = 9
    build_cost_single_story = 320  # $/sq ft
    build_cost_two_story = 340  # $/sq ft


class BuildableUnit(RentalUnit):
    # commented out fields inherited
    # sqft: int
    # br: int
    # ba: int
    stories: int
    lotspace_required: int
    constr_costs: ConstructionCosts

    @property
    def hard_build_cost(self):
        return self.sqft * self.hard_cost_per_sqft

    @property
    def hard_cost_per_sqft(self):
        assert self.stories in [1, 2]
        return self.constr_costs.build_cost_two_story if self.stories == 2 else \
            self.constr_costs.build_cost_single_story


def get_build_specs(constr_costs: ConstructionCosts) -> List[BuildableUnit]:
    # Types of units that can be built
    sm_adu_build = BuildableUnit(sqft=750, br=2, ba=1, stories=1, lotspace_required=800, constr_costs=constr_costs)
    lg_adu_build = BuildableUnit(sqft=1200, br=3, ba=2, stories=1, lotspace_required=1300,
                                 constr_costs=constr_costs)
    sm_adu_2story_build = BuildableUnit(sqft=750, br=2, ba=1, stories=2, lotspace_required=400,
                                        constr_costs=constr_costs)
    lg_adu_2story_build = BuildableUnit(sqft=1200, br=3, ba=2, stories=2, lotspace_required=700,
                                        constr_costs=constr_costs)
    builds = [sm_adu_build, lg_adu_build, sm_adu_2story_build, lg_adu_2story_build]
    return builds


class ReParams(BaseModel):
    # Rent related
    existing_unit_rent_percentile: int = 50
    new_unit_rent_percentile: int = 90
    vacancy_rate: float = 0.05  # fraction of rent

    # Operations related
    insurance_cost_rate: float = 0.002  # fraction of house + construction cost
    repair_cost_rate: float = 0.08  # fraction of rent
    mgmt_cost_rate: float = 0.08  # fraction of rent
    prop_tax_rate: float = 0.0125  # fraction of house + construction cost

    # Construction related
    constr_costs = ConstructionCosts()
