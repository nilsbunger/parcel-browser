# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models

from elt.models.model_utils import SanitizedRawModelMixin


class RawReportall(SanitizedRawModelMixin, models.Model):
    class Meta:
        verbose_name = "Raw Reportall [Shapefile]"
        verbose_name_plural = "Raw Reportall [Shapefile]"
        indexes = [models.Index(fields=["parcel_id"])]

    class CountyEnum(models.TextChoices):
        SF = "SFC", "San Francisco"

    cty_row_id = models.BigIntegerField(null=True, blank=True)
    parcel_id = models.CharField(max_length=50, null=True, blank=True)
    county = models.CharField(choices=CountyEnum.choices, null=True, blank=True)
    county_nam = models.CharField(max_length=100, null=True, blank=True)
    county_fip = models.BigIntegerField(null=True, blank=True)
    state_abbr = models.CharField(max_length=2, null=True, blank=True)
    situs = models.CharField(max_length=254, null=True, blank=True)
    addr_number = models.CharField(max_length=100, null=True, blank=True)
    addr_street = models.CharField(max_length=100, null=True, blank=True)
    addr_st_01 = models.CharField(max_length=100, null=True, blank=True)
    addr_st_02 = models.CharField(max_length=20, null=True, blank=True)
    addr_st_03 = models.CharField(max_length=20, null=True, blank=True)
    addr_sec_u = models.CharField(max_length=32, null=True, blank=True)
    addr_se_01 = models.CharField(max_length=32, null=True, blank=True)
    situs_city = models.CharField(max_length=28, null=True, blank=True)
    situs_zip = models.CharField(max_length=5, null=True, blank=True)
    situs_zip4 = models.CharField(max_length=4, null=True, blank=True)
    muni_name = models.CharField(max_length=100, null=True, blank=True)
    owner = models.CharField(max_length=100, null=True, blank=True)
    trans_date = models.DateField(null=True, blank=True)
    sale_price = models.FloatField(null=True, blank=True)
    bldg_sqft = models.BigIntegerField(null=True, blank=True)
    story_height = models.FloatField(null=True, blank=True)
    ngh_code = models.CharField(max_length=20, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    land_use_class = models.CharField(max_length=60, null=True, blank=True)
    land_us_01 = models.CharField(max_length=50, null=True, blank=True)
    school_dis = models.CharField(max_length=100, null=True, blank=True)
    mkt_val_land = models.FloatField(null=True, blank=True)
    mkt_val_bldg = models.FloatField(null=True, blank=True)
    mkt_val_total = models.FloatField(null=True, blank=True)
    acreage = models.FloatField(null=True, blank=True)
    calc_acrea = models.FloatField(null=True, blank=True)
    fld_zone = models.CharField(max_length=254, null=True, blank=True)
    zone_subty = models.CharField(max_length=254, null=True, blank=True)
    routing_nu = models.CharField(max_length=25, null=True, blank=True)
    map_book = models.CharField(max_length=25, null=True, blank=True)
    map_page = models.CharField(max_length=25, null=True, blank=True)
    mail_name = models.CharField(max_length=100, null=True, blank=True)
    mail_address = models.CharField(max_length=254, null=True, blank=True)
    mail_ad_01 = models.CharField(max_length=254, null=True, blank=True)
    mail_ad_02 = models.CharField(max_length=254, null=True, blank=True)
    m_recpnt = models.CharField(max_length=64, null=True, blank=True)
    m_uspsbox = models.CharField(max_length=26, null=True, blank=True)
    m_addressn = models.CharField(max_length=13, null=True, blank=True)
    m_streetpr = models.CharField(max_length=17, null=True, blank=True)
    m_streetnm = models.CharField(max_length=59, null=True, blank=True)
    m_streetpo = models.CharField(max_length=11, null=True, blank=True)
    m_streetpd = models.CharField(max_length=9, null=True, blank=True)
    m_subocc = models.CharField(max_length=37, null=True, blank=True)
    m_placenm = models.CharField(max_length=49, null=True, blank=True)
    m_statenm = models.CharField(max_length=14, null=True, blank=True)
    m_zipcode = models.CharField(max_length=11, null=True, blank=True)
    m_country = models.CharField(max_length=6, null=True, blank=True)
    legal_desc = models.CharField(max_length=254, null=True, blank=True)
    legal_d_01 = models.CharField(max_length=254, null=True, blank=True)
    legal_d_02 = models.CharField(max_length=254, null=True, blank=True)
    buildings = models.BigIntegerField(null=True, blank=True)
    year_built = models.BigIntegerField(null=True, blank=True)
    eff_year_b = models.BigIntegerField(null=True, blank=True)
    style = models.CharField(max_length=50, null=True, blank=True)
    exterior = models.CharField(max_length=50, null=True, blank=True)
    condition = models.CharField(max_length=50, null=True, blank=True)
    heatsrc = models.CharField(max_length=20, null=True, blank=True)
    cooling = models.CharField(max_length=20, null=True, blank=True)
    total_room = models.BigIntegerField(null=True, blank=True)
    bedrooms = models.BigIntegerField(null=True, blank=True)
    halfbath = models.FloatField(null=True, blank=True)
    fullbath = models.FloatField(null=True, blank=True)
    total_bath = models.FloatField(null=True, blank=True)
    water = models.CharField(max_length=20, null=True, blank=True)
    sewer = models.CharField(max_length=20, null=True, blank=True)
    zoning = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    elevation = models.FloatField(null=True, blank=True)
    owner_occ = models.CharField(max_length=1, null=True, blank=True)
    robust_id = models.CharField(max_length=16, null=True, blank=True)
    usps_resid = models.CharField(max_length=11, null=True, blank=True)
    alt_id_1 = models.CharField(max_length=50, null=True, blank=True)
    alt_id_2 = models.CharField(max_length=50, null=True, blank=True)
    census_pla = models.CharField(max_length=18, null=True, blank=True)
    last_updat = models.CharField(max_length=7, null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326)
    run_date = models.DateField()


raw_reportall_mapping = {
    "acreage": "ACREAGE",
    "addr_number": "ADDR_NUMBE",
    "addr_se_01": "ADDR_SE_01",
    "addr_sec_u": "ADDR_SEC_U",
    "addr_st_01": "ADDR_ST_01",
    "addr_st_02": "ADDR_ST_02",
    "addr_st_03": "ADDR_ST_03",
    "addr_street": "ADDR_STREE",
    "alt_id_1": "ALT_ID_1",
    "alt_id_2": "ALT_ID_2",
    "bedrooms": "BEDROOMS",
    "bldg_sqft": "BLDG_SQFT",
    "buildings": "BUILDINGS",
    "calc_acrea": "CALC_ACREA",
    "census_pla": "CENSUS_PLA",
    "condition": "CONDITION",
    "cooling": "COOLING",
    "county_fip": "COUNTY_FIP",
    "county_nam": "COUNTY_NAM",
    "cty_row_id": "CTY_ROW_ID",
    "eff_year_b": "EFF_YEAR_B",
    "elevation": "ELEVATION",
    "exterior": "EXTERIOR",
    "fld_zone": "FLD_ZONE",
    "fullbath": "FULLBATH",
    "geom": "MULTIPOLYGON",
    "halfbath": "HALFBATH",
    "heatsrc": "HEATSRC",
    "land_us_01": "LAND_US_01",
    "land_use_class": "LAND_USE_C",
    "last_updat": "LAST_UPDAT",
    "latitude": "LATITUDE",
    "legal_d_01": "LEGAL_D_01",
    "legal_d_02": "LEGAL_D_02",
    "legal_desc": "LEGAL_DESC",
    "longitude": "LONGITUDE",
    "m_addressn": "M_ADDRESSN",
    "m_country": "M_COUNTRY",
    "m_placenm": "M_PLACENM",
    "m_recpnt": "M_RECPNT",
    "m_statenm": "M_STATENM",
    "m_streetnm": "M_STREETNM",
    "m_streetpd": "M_STREETPD",
    "m_streetpo": "M_STREETPO",
    "m_streetpr": "M_STREETPR",
    "m_subocc": "M_SUBOCC",
    "m_uspsbox": "M_USPSBOX",
    "m_zipcode": "M_ZIPCODE",
    "mail_ad_01": "MAIL_AD_01",
    "mail_ad_02": "MAIL_AD_02",
    "mail_address": "MAIL_ADDRE",
    "mail_name": "MAIL_NAME",
    "map_book": "MAP_BOOK",
    "map_page": "MAP_PAGE",
    "mkt_val_bldg": "MKT_VAL_BL",
    "mkt_val_land": "MKT_VAL_LA",
    "mkt_val_total": "MKT_VAL_TO",
    "muni_name": "MUNI_NAME",
    "ngh_code": "NGH_CODE",
    "owner": "OWNER",
    "owner_occ": "OWNER_OCCU",
    "parcel_id": "PARCEL_ID",
    "robust_id": "ROBUST_ID",
    "routing_nu": "ROUTING_NU",
    "sale_price": "SALE_PRICE",
    "school_dis": "SCHOOL_DIS",
    "sewer": "SEWER",
    "situs": "SITUS",
    "situs_city": "SITUS_CITY",
    "situs_zip": "SITUS_ZIP",
    "situs_zip4": "SITUS_ZIP4",
    "state_abbr": "STATE_ABBR",
    "story_height": "STORY_HEIG",
    "style": "STYLE",
    "total_bath": "TOTAL_BATH",
    "total_room": "TOTAL_ROOM",
    "trans_date": "TRANS_DATE",
    "usps_resid": "USPS_RESID",
    "water": "WATER",
    "year_built": "YEAR_BUILT",
    "zip_code": "ZIP_CODE",
    "zone_subty": "ZONE_SUBTY",
    "zoning": "ZONING",
}
