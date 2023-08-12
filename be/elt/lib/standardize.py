import csv
import re
import sys
import traceback
from datetime import date

from more_itertools import collapse
from ninja import Field, Schema

from elt.models import RawSfHeTableB, RawSfRentboardHousingInv


def enum_or_none(_Enum, _val):  # noqa: N803
    return _Enum(_val) if _val is not None else None


def round_or_none(_val, ndigits):
    return round(_val, ndigits) if _val is not None else None


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

ContactType = RawSfRentboardHousingInv.ContactTypeEnum
ContactRole = RawSfRentboardHousingInv.ContactAssociationEnum


class RentBoardEntry(Schema):
    """Accept a RawSfRentboardHousingInv objct (eg RawSfRentboardHousingInv.from_orm(obj)), and pull out useful info."""

    apn: str = Field(..., alias="parcel_number")
    contact_name: str | None
    contact_phone: str | None = Field(..., alias="phone")
    contact_email: str | None = Field(..., alias="email")
    contact_type: ContactType | None = Field(..., alias="contact_type")
    contact_role: ContactRole | None = Field(..., alias="contact_association")
    rent: int | None

    # br: int
    # bath: int
    # sq_ft: int
    # unit_number: str
    # unit_address: str
    # # rent_includes: # add this later
    # rent_date: date
    # occupancy_type: RawSfRentboardHousingInv.OccupancyTypeEnum
    # vacancy_date: date
    # occupancy_comment: str

    def resolve_rent(self, obj):
        if not obj.monthly_rent:
            return None
        if obj.monthly_rent == RawSfRentboardHousingInv.MonthlyRentEnum.A0_NO_RENT_PAID_BY_THE_OCCUPANT:
            return 0
        if obj.monthly_rent == RawSfRentboardHousingInv.MonthlyRentEnum.A7000:
            return 8000  # $7000 or more... pick a number.

        match_obj = re.search(r"(\d+) (\d+)", obj.get_monthly_rent_display())
        try:
            rent_range = (int(match_obj.group(1)), int(match_obj.group(2)))
            return (rent_range[0] + rent_range[1]) / 2
        except Exception:
            print("Couldn't match rent range", obj.get_monthly_rent_display())
            raise

    def resolve_contact_name(self, obj):
        if not obj.first_name and not obj.last_name:
            return None
        return f"{obj.first_name + ' ' if obj.first_name else ''}{obj.last_name or ''}"


sf_he_facts_zoning_map = {
    "55' Height Allowed": 55,
    "65' Height Allowed": 65,
    "65' Height Allowed (Unchanged)": 65,
    "80' Height Allowed (Unchanged)": 80,
    "85' Height Allowed": 85,
    "100' Height Allowed (Unchanged)": 100,
    "85' Height Allowed (Unchanged)": 85,
    "105' Height Allowed (Unchanged)": 105,
    "130' Height Allowed (Unchanged)": 130,
    "140' Height Allowed": 140,
    "240' Height Allowed": 240,
    "300' Height Allowed": 300,
    "Increased density up to four units (six units on corner lots)": "4-6 Units",
    "No height change, density decontrol": "Density Decontrol",
}


class SfHeFacts(Schema):
    """Accept a list of RawGeomData sf he objects that map to a single parcel (via SfHeFacts.from_orm(objlist)),
    and pull out useful info."""

    apn: str
    hes_count: int
    he_zoning: tuple[str | int | None, ...]
    curr_zoning: str | None  # eg "C-2" , "RH-2", ...

    def resolve_apn(self, objlist):
        assert all([o.data["mapblklot"] == objlist[0].data["mapblklot"] for o in objlist])
        if objlist[0].data["mapblklot"] is None:
            print("HMMM")
        return objlist[0].data["mapblklot"]

    def resolve_hes_count(self, objlist):
        # it's better to count the classified entries from self.he_zoning since the table has wonky entries
        return len([x for x in self.he_zoning if x])

    def resolve_he_zoning(self, objlist):
        # Return tuple of 2 values -- concept A and concept B
        retval = [None, None]
        for obj in objlist:
            he_zoning_raw = obj.data.get("DAG188", obj.data.get("DAG199", obj.data.get("FOURPLEX")))
            assert he_zoning_raw
            he_zoning = sf_he_facts_zoning_map.get(he_zoning_raw, None)
            assert he_zoning
            if "1_A" in obj.data["LAYER"]:
                retval[0] = he_zoning
            elif "1_B" in obj.data["LAYER"]:
                retval[1] = he_zoning
            else:
                raise Exception(f"Unknown layer {obj.data['LAYER']}")
        return retval

    def resolve_curr_zoning(self, objlist):
        assert all([o.data["zoning"] == objlist[0].data["zoning"] for o in objlist])
        return objlist[0].data["zoning"]


class ParcelFacts(Schema):
    """Accept a RawSfParcelWrap objct (via ParcelFacts.from_orm(obj)), and pull out useful info."""

    apn: str
    address: str = Field(..., alias="parcel.resolved_address")
    parcel_sq_ft: int
    curr_zoning: str = Field(..., alias="parcel.zoning_cod")
    curr_use: str | None = Field(..., alias="reportall_parcel.land_use_class")
    net_build_sq_ft: int | None
    sq_ft_ratio: float | None
    hes_count: int
    he_zoning: tuple[str | int | None, ...]
    he_gp_type: tuple[str | None, ...]
    he_max_density: tuple[float | None, ...]
    year_built: int = Field(..., alias="reportall_parcel.year_built")
    bluesky_prob: float | None
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
    rent_board_data: list[RentBoardEntry]
    vacant_count: int | None
    owner_occ_count: int | None
    rented_count: int | None
    non_resi_count: int | None

    @staticmethod
    def get_occupancy_count(obj, occ_type):
        # If there's no rent board data, return None to differentiate from 0 reports of a type.
        if not obj.rawsfrentboardhousinginv_set.all():
            return None
        return len([x for x in obj.rawsfrentboardhousinginv_set.all() if x.occupancy_type == occ_type])

    @staticmethod
    def resolve_vacant_count(obj):
        return ParcelFacts.get_occupancy_count(obj, RawSfRentboardHousingInv.OccupancyTypeEnum.VACANT)

    @staticmethod
    def resolve_owner_occ_count(obj):
        return ParcelFacts.get_occupancy_count(obj, RawSfRentboardHousingInv.OccupancyTypeEnum.OCCUPIED_BY_OWNER)

    @staticmethod
    def resolve_rented_count(obj):
        return ParcelFacts.get_occupancy_count(obj, RawSfRentboardHousingInv.OccupancyTypeEnum.OCCUPIED_BY_NON_OWNER)

    @staticmethod
    def resolve_non_resi_count(obj):
        return ParcelFacts.get_occupancy_count(obj, RawSfRentboardHousingInv.OccupancyTypeEnum.NON_RESIDENTIAL)

    def resolve_rent_board_data(self, obj):
        rent_entries = [RentBoardEntry.from_orm(rent_entry) for rent_entry in obj.rawsfrentboardhousinginv_set.all()]
        return rent_entries

    def resolve_existing_gp_type(self, obj):
        return obj.he_table_b.get_ex_gp_type_display()

    def resolve_bluesky_prob(self, obj):
        return None
        # From dec '22 housing element - outdated:
        # if obj.he_table_a is None or obj.he_table_a.opt2 is None:
        #     return None
        # return round(obj.he_table_a.opt2 * 100, ndigits=2)

    def resolve_he_gp_type(self, obj):
        return [None, None]
        # From dec '22 housing element - outdated:
        # he_gp_type = [getattr(obj.he_table_b, f"get_m{idx}_gp_type_display")() for idx in (1, 2, 3)]
        # return he_gp_type

    def resolve_he_zoning(self, obj, *args):
        return obj.he_facts.he_zoning  # eg ('65', '65') for concept a and b

        # From dec '22 housing element - outdated:
        # he_zoning = [
        #     zoning_map[enum_or_none(ZoningEnum, getattr(obj.he_table_b, f"m{idx}_zoning"))] for idx in (1, 2, 3)
        # ]
        # return he_zoning

    def resolve_he_max_density(self, obj):
        return [None, None]
        # From dec '22 housing element - outdated:
        # he_max_density = [round_or_none(getattr(obj.he_table_b, f"m{idx}_maxdens"), ndigits=1) for idx in (1, 2, 3)]
        # return he_max_density

    def resolve_hes_count(self, obj):
        return obj.he_facts.hes_count
        # From dec '22 housing element - outdated:
        # hes = self.he_zoning
        # return len([he for he in hes if he is not None])

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

    def resolve_net_build_sq_ft(self, obj):
        numeric_upzones = [int(x) for x in self.he_zoning if x is not None and x.isnumeric()]
        if not len(numeric_upzones):
            # TODO: calculate buildable sq ft for non-numeric upzones (density decontrol, etc)
            return None

        max_height = max(numeric_upzones)
        floors = max_height // 10
        net_sqft = round(0.9 * 0.85 * self.parcel_sq_ft * floors)
        return net_sqft

    def resolve_sq_ft_ratio(self, obj):
        if str(self.net_build_sq_ft).isnumeric():
            bldg_sq_ft = max(obj.reportall_parcel.bldg_sqft, 1000)
            x = round(self.net_build_sq_ft / bldg_sq_ft, ndigits=1)
            return x
        # TODO: calculate buildable sq ft for non-numeric upzones (density decontrol, etc)
        return None


def create_parcel_facts_csv(schema_list: list[ParcelFacts], filename: str):
    """Create a CSV file from a list of ParcelFacts objects, including relevant related data.
    This should be similar to the data we'd show in a detailed parcel view."""
    fieldnames = list(schema_list[0].dict().keys())
    fieldnames.remove("rent_board_data")
    fieldnames += collapse(
        [
            (f"contact_name{i}", f"contact_email{i}", f"contact_phone{i}", f"contact_role{i}", f"contact_type{i}")
            for i in [1, 2, 3, 4]
        ]
    )

    # Create the CSV file
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore", restval=None)

        writer.writeheader()
        for row in schema_list:
            row_dict = dict(vars(row))  # dict() to make a copy
            if row.rent_board_data:
                deduped_contacts = {
                    (r.contact_name, r.contact_email, r.contact_phone, r.contact_role, r.contact_type)
                    for r in row.rent_board_data
                    if r.contact_name
                }
                for i, contact in enumerate(list(deduped_contacts)[:4], start=1):
                    row_dict[f"contact_name{i}"] = contact[0]
                    row_dict[f"contact_email{i}"] = contact[1]
                    row_dict[f"contact_phone{i}"] = contact[2]
                    row_dict[f"contact_role{i}"] = contact[3].label if contact[3] else None
                    row_dict[f"contact_type{i}"] = contact[4].label if contact[4] else None
            writer.writerow(row_dict)
    print(f"Done writing file {filename}")
