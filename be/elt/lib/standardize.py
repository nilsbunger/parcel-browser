from datetime import date
import sys
import traceback
from typing import Optional, Tuple

from elt.models import RawSfHeTableB
from ninja import Field, Schema


enum_or_none = lambda _Enum, _val: _Enum(_val) if _val is not None else None
round_or_none = lambda _val, ndigits: round(_val, ndigits) if _val is not None else None

ZoningEnum = RawSfHeTableB.ZoningEnum
zoning_map = {
    ZoningEnum.A240HeightAllowed: 240,
    ZoningEnum.A140HeightAllowed: 140,
    ZoningEnum.A85HeightAllowed: 85,
    ZoningEnum.A65HeightAllowed: 65,
    ZoningEnum.A55HeightAllowed: 55,
    ZoningEnum.AddedHeightInExistingFormBasedArea: "Height Added Form Based",
    ZoningEnum.IncreasedDensityUpToFourUnitsSixUnitsOnCornerLots: "4-6 Units",
    ZoningEnum.NoHeightChangeDensityDecontrol: "Density Decontrol",
    None: None,
}


class ParcelFacts(Schema):
    """Accept a RawSfParcelWrap objct (eg ParcelFacts.from_orm(obj)), and pull out useful info."""

    apn: str
    address: str = Field(..., alias="parcel.resolved_address")
    parcel_sq_ft: int
    curr_zoning: str = Field(..., alias="parcel.zoning_cod")
    curr_use: str | None = Field(..., alias="reportall_parcel.land_use_class")
    c_net_build_sq_ft: int | str
    c_sq_ft_ratio: float | str
    c_num_hes: int
    he_zoning: Tuple[str | int | None, str | int | None, str | int | None]
    he_gp_type: Tuple[str | None, str | None, str | None]
    he_max_density: Tuple[float | None, float | None, float | None]
    year_built: int = Field(..., alias="reportall_parcel.year_built")
    bluesky_prob: Optional[float]
    # curr__gp_type: str ## this info is in the curr_zoning
    building_sqft: int = Field(..., alias="reportall_parcel.bldg_sqft")
    building_br: int = Field(..., alias="reportall_parcel.bedrooms")
    building_bath: int | None = Field(..., alias="reportall_parcel.total_bath")
    owner_occ: bool = Field(..., alias="reportall_parcel.owner_occ")
    owner_name: str = Field(..., alias="reportall_parcel.owner")
    owner_address: str = Field(..., alias="reportall_parcel.mail_address")
    owner_citystatezip: str | None = Field(..., alias="reportall_parcel.mail_ad_02")
    last_sale_price: int = Field(..., alias="reportall_parcel.sale_price")
    last_sale_date: date | None = Field(..., alias="reportall_parcel.trans_date")
    curr_val_bldg: int = Field(..., alias="reportall_parcel.mkt_val_bldg")
    curr_val_land: int = Field(..., alias="reportall_parcel.mkt_val_land")

    def resolve_existing_gp_type(self, obj):
        return getattr(obj.he_table_b, "get_ex_gp_type_display")()

    def resolve_bluesky_prob(self, obj):
        if obj.he_table_a is None or obj.he_table_a.opt2 is None:
            return None
        return round(obj.he_table_a.opt2 * 100, ndigits=2)

    def resolve_he_gp_type(self, obj):
        he_gp_type = [getattr(obj.he_table_b, f"get_m{idx}_gp_type_display")() for idx in (1, 2, 3)]
        return he_gp_type

    def resolve_he_zoning(self, obj):
        he_zoning = [
            zoning_map[enum_or_none(ZoningEnum, getattr(obj.he_table_b, f"m{idx}_zoning"))] for idx in (1, 2, 3)
        ]
        return he_zoning

    def resolve_he_max_density(self, obj):
        he_max_density = [round_or_none(getattr(obj.he_table_b, f"m{idx}_maxdens"), ndigits=1) for idx in (1, 2, 3)]
        return he_max_density

    def resolve_parcel_sq_ft(self, obj):
        try:
            assert obj.reportall_parcel.condition is None
            assert obj.reportall_parcel.mail_name is None
            assert obj.reportall_parcel.mail_ad_01 is None
            return obj.reportall_parcel.calc_acrea * 43560
        except AssertionError as e:
            _, _, tb = sys.exc_info()
            traceback.print_tb(tb)  # Fixed format
            print(e)
            raise e

    def resolve_c_num_hes(self, obj):
        hes = self.he_zoning
        return len([he for he in hes if he is not None])

    def resolve_c_net_build_sq_ft(self, obj):
        numeric_upzones = [int(x) for x in self.he_zoning if x is not None and x.isnumeric()]
        if not len(numeric_upzones):
            # TODO: calculate buildable sq ft for non-numeric upzones (density decontrol, etc)
            return "0000 NOT CALCULATED"

        max_height = max(numeric_upzones)
        floors = max_height // 10
        net_sqft = round(0.9 * 0.85 * self.parcel_sq_ft * floors)
        return net_sqft

    def resolve_c_sq_ft_ratio(self, obj):
        if str(self.c_net_build_sq_ft).isnumeric():
            bldg_sq_ft = max(obj.reportall_parcel.bldg_sqft, 1000)
            x = round(self.c_net_build_sq_ft / bldg_sq_ft, ndigits=1)
            return x
        return "0000 NOT CALCULATED"
