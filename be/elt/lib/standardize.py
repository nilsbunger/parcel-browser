import csv
import re
import sys
import traceback
from datetime import date

from dateutil.parser import parse as date_parse
from lib.util import flatten_dict
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
    unit_address: str
    unit_number: str | None
    br: int | None = Field(..., alias="bedroom_count")
    ba: int | None = Field(..., alias="bathroom_count")
    rent_date: date | int | None  # when it's just an int, it's the year, and it means we don't know the month.
    sig_date: date | None = Field(..., alias="signature_date1")
    sig_date2: date | None = Field(..., alias="signature_date2")
    sqft: int | None
    # # rent_includes: # add this later
    occupancy_type: RawSfRentboardHousingInv.OccupancyTypeEnum
    vacancy_date: date | None
    # occupancy_comment: str

    def resolve_vacancy_date(self, obj):
        try:
            return date_parse(obj.vacancy_date).date() if obj.vacancy_date else None
        except Exception as e:  # noqa: F841 - unused variable e
            if x := re.search(r"\b(\d\d)/(\d\d)/(\d\d\d\d)\b", obj.vacancy_date):
                year = int(x.group(3))
                if 1950 < year < 2030:
                    return date(year, int(x.group(1)), int(x.group(2)))
            if "00/00/00" in obj.vacancy_date:
                return None
            print("Unparseable vacancy date:", obj.vacancy_date)
            return None

    def resolve_sqft(self, obj):
        if obj.square_footage in [None, RawSfRentboardHousingInv.SquareFootageEnum.UNKNOWN]:
            return None
        sqft_str = obj.get_square_footage_display()
        assert sqft_str[0] == "A"
        min_sqft, max_sqft, *_ = sqft_str[1:].split(" ")
        assert min_sqft.isdigit()
        if max_sqft.isdigit():
            return (int(min_sqft) + int(max_sqft)) / 2
        return int(min_sqft) * 1.15  # when there is no max, assume unit is 15% larger than min.

    def resolve_rent_date(self, obj):  # noqa: PLR0911 too many return statements
        yr_enum = RawSfRentboardHousingInv.YearEnum
        if obj.year is None:
            return None
        match obj.year:
            case None | yr_enum.NO_INFO:
                return None
            case yr_enum.MORE_THAN_20_YEARS:
                return 1995
            case yr_enum.WITHIN_PAST_10_20_YEARS:
                return 2009
            case yr_enum.WITHIN_PAST_5_10_YEARS:
                return 2017
            case yr_enum.WITHIN_PAST_5_YEARS:
                return 2020
        try:
            return date(obj.year, obj.month, obj.day)
        except Exception as e:
            if obj.year > 1950 and obj.year < 2025:
                return obj.year
            print(f"unknown year {obj.year}")
            raise e from e

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


class SfHeEntry(Schema):
    """Accept a list of RawGeomData sf he objects that map to a single parcel (via SfHeFacts.from_orm(objlist)),
    and pull out useful info."""

    apn: str
    hes_count: int
    he_zoning: tuple[str | int | None, ...]
    curr_zoning: str | None  # eg "C-2" , "RH-2", ...

    def resolve_apn(self, objlist):
        assert len(objlist), "Can't construct an SfHeEntry with no objects"
        assert all([o.data["mapblklot"] == objlist[0].data["mapblklot"] for o in objlist])
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
    year_built: int = Field(..., alias="reportall_parcel.year_built")
    bluesky_prob: float | None
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
    he_data: SfHeEntry | None
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

    def resolve_existing_gp_type(self, obj):
        return obj.he_table_b.get_ex_gp_type_display()

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
        if not self.he_data:
            return None
        numeric_upzones = [int(x) for x in self.he_data.he_zoning if x is not None and x.isnumeric()]
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

    def resolve_rent_board_data(self, obj):
        """Resolve embedded rent_board list"""
        rent_entries = [RentBoardEntry.from_orm(rent_entry) for rent_entry in obj.rawsfrentboardhousinginv_set.all()]
        return rent_entries

    def resolve_he_data(self, obj):
        """Resolve embedded housing element list. Takes list of related RawGeomData objects and combines into one entry.."""
        if len(obj.rawgeomdata_set.all()) == 0:
            return None
        he_data = SfHeEntry.from_orm(obj.rawgeomdata_set.all())
        return he_data


def create_parcel_facts_csv(schema_list: list[ParcelFacts], filename: str):
    """Create a CSV file from a list of ParcelFacts objects, including relevant related data.
    This should be similar to the data we'd show in a detailed parcel view."""

    # construct column names we want - for rent-board data only include contact info
    # representative row with all columns we want
    rep_row_keys = flatten_dict(next(s for s in schema_list if s.rent_board_data and s.he_data).dict()).keys()

    fieldnames = [k for k in rep_row_keys if "rent_board_data" not in k and k != "he_data.apn"]
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
            row_dict = flatten_dict(row.dict())
            if row.rent_board_data:
                # rent board entries may be for different units but have same contact. dedup the contact info here.
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
