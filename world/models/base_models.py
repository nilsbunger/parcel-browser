from typing import List

from django.contrib.gis.db import models
from pydantic import BaseModel


class BuildingOutlines(models.Model):
    outline_id = models.FloatField()
    bldgid = models.FloatField()
    centroid_x = models.FloatField()
    centroid_y = models.FloatField()
    area = models.FloatField()
    comment = models.CharField(max_length=254, blank=True, null=True)
    shape_leng = models.FloatField()
    shape_star = models.FloatField()
    shape_stle = models.FloatField()
    geom = models.MultiPolygonField(srid=4326)


class ZoningBase(models.Model):
    zone_name = models.CharField(max_length=20)
    imp_date = models.DateField()
    ordnum = models.CharField(max_length=10)
    shape_star = models.FloatField()
    shape_stle = models.FloatField()
    geom = models.MultiPolygonField(srid=4326)


class RentalUnit(BaseModel):
    br: int
    ba: int
    sqft: int

    # make class hashable by implementing __eq__ and __hash__
    def __eq__(self, other):
        return other.br == self.br and other.ba == self.ba and other.sqft == self.sqft

    def __hash__(self):
        return hash((self.br, self.ba, self.sqft))


class Parcel(models.Model):
    apn = models.CharField(max_length=10, blank=True, null=True, unique=True)
    apn_8 = models.CharField(max_length=8, blank=True, null=True)
    parcelid = models.BigIntegerField()
    own_name1 = models.CharField(max_length=96, blank=True, null=True)
    own_name2 = models.CharField(max_length=50, blank=True, null=True)
    own_name3 = models.CharField(max_length=50, blank=True, null=True)
    fractint = models.FloatField()
    own_addr1 = models.CharField(max_length=75, blank=True, null=True)
    own_addr2 = models.CharField(max_length=50, blank=True, null=True)
    own_addr3 = models.CharField(max_length=50, blank=True, null=True)
    own_addr4 = models.CharField(max_length=50, blank=True, null=True)
    own_zip = models.CharField(max_length=9, blank=True, null=True)
    situs_juri = models.CharField(max_length=2, blank=True, null=True)
    situs_stre = models.CharField(max_length=30, blank=True, null=True)
    situs_suff = models.CharField(max_length=4, blank=True, null=True)
    situs_post = models.CharField(max_length=2, blank=True, null=True)
    situs_pre_field = models.CharField(max_length=2, blank=True, null=True)
    situs_addr = models.BigIntegerField()
    situs_frac = models.CharField(max_length=3, blank=True, null=True)
    situs_buil = models.CharField(max_length=4, blank=True, null=True)
    situs_suit = models.CharField(max_length=6, blank=True, null=True)
    legldesc = models.CharField(max_length=65, blank=True, null=True)
    asr_land = models.BigIntegerField()
    asr_impr = models.BigIntegerField()
    asr_total = models.BigIntegerField()
    doctype = models.CharField(max_length=1, blank=True, null=True)
    docnmbr = models.CharField(max_length=6, blank=True, null=True)
    docdate = models.CharField(max_length=8, blank=True, null=True)
    acreage = models.FloatField()
    taxstat = models.CharField(max_length=1, blank=True, null=True)
    ownerocc = models.CharField(max_length=1, blank=True, null=True)
    tranum = models.CharField(max_length=5, blank=True, null=True)
    asr_zone = models.IntegerField()
    asr_landus = models.IntegerField()
    unitqty = models.IntegerField()
    submap = models.CharField(max_length=11, blank=True, null=True)
    subname = models.CharField(max_length=64, blank=True, null=True)
    nucleus_zo = models.CharField(max_length=2, blank=True, null=True)
    nucleus_us = models.CharField(max_length=3, blank=True, null=True)
    situs_comm = models.CharField(max_length=28, blank=True, null=True)
    year_effec = models.CharField(max_length=2, blank=True, null=True)
    total_lvg_field = models.BigIntegerField()
    bedrooms = models.CharField(max_length=3, blank=True, null=True)
    baths = models.CharField(max_length=3, blank=True, null=True)
    addition_a = models.BigIntegerField()
    garage_con = models.CharField(max_length=1, blank=True, null=True)
    garage_sta = models.CharField(max_length=3, blank=True, null=True)
    carport_st = models.CharField(max_length=3, blank=True, null=True)
    pool = models.CharField(max_length=1, blank=True, null=True)
    par_view = models.CharField(max_length=1, blank=True, null=True)
    usable_sq_field = models.CharField(max_length=5, blank=True, null=True)
    qual_class = models.CharField(max_length=5, blank=True, null=True)
    nucleus_si = models.BigIntegerField()
    nucleus_1 = models.BigIntegerField()
    nucleus_2 = models.CharField(max_length=3, blank=True, null=True)
    situs_zip = models.CharField(max_length=10, blank=True, null=True)
    x_coord = models.FloatField()
    y_coord = models.FloatField()
    overlay_ju = models.CharField(max_length=2)
    sub_type = models.IntegerField()
    multi = models.CharField(max_length=1, blank=True, null=True)
    shape_star = models.FloatField()
    shape_stle = models.FloatField()
    geom = models.MultiPolygonField(srid=4326, blank=True, null=True)

    @property
    def garages(self) -> int:
        return int(self.garage_sta) if self.garage_sta else 0

    @property
    def carports(self) -> int:
        return int(self.carport_st) if self.carport_st else 0

    @property
    def address(self) -> str:
        fields = [
            str(self.situs_addr),
            self.situs_pre_field or None,
            self.situs_stre,
            self.situs_suff or None,
            self.situs_post or None,
        ]
        fields = [f for f in fields if f]
        return " ".join(fields)

    @property
    def ba(self) -> float:
        if self.baths:
            return float(self.baths) / 10.0
        else:
            return 0.0

    @property
    def br(self) -> int:
        if self.bedrooms:
            return int(self.bedrooms)
        else:
            return 0

    @property
    def sqft(self) -> int:
        if self.total_lvg_field:
            return int(self.total_lvg_field)
        else:
            return -1

    @property
    def rental_units(self) -> List[RentalUnit]:
        # Use parcel data to construct likely combination of units.
        # TODO: support overrides of this data
        if self.unitqty == 0:
            return []
        if self.unitqty == 1:
            return [RentalUnit(br=self.br, ba=self.ba, sqft=self.sqft)]
        per_unit_sqft = self.sqft / self.unitqty if self.sqft > -1 else -1
        retval = [
            RentalUnit(br=self.br / self.unitqty, ba=self.ba / self.unitqty, sqft=per_unit_sqft)
            for i in range(self.unitqty)
        ]
        # Remainder could be large in a multi-unit property, so distribute the remainder evenly
        for i in range(0, int(self.br % self.unitqty)):
            retval[i].br += 1
        for i in range(0, int(self.ba % self.unitqty)):
            retval[i].ba += 1
        return retval

    def __str__(self):
        if self.acreage > 0:
            lot_str = "%s acres" % self.acreage
        else:
            lot_str = "%s lot" % self.usable_sq_field
        base_str = "%s %s %s: %s living, " % (
            self.apn,
            self.address,
            self.situs_zip,
            self.total_lvg_field,
        )
        return base_str + lot_str

    class Meta:
        indexes = [models.Index(fields=["apn"]), models.Index(fields=["situs_addr"])]


class TopographyLoads(models.Model):
    fname = models.CharField("filename", max_length=200)
    extents = models.PolygonField(srid=4326, unique=True)
    # note: only updated on model.save
    run_date = models.DateField(auto_now=True)


class Topography(models.Model):
    elev = models.FloatField()
    ltype = models.IntegerField()
    index_field = models.IntegerField()
    shape_length = models.FloatField()
    geom = models.MultiLineStringField(srid=4326)


class Roads(models.Model):
    fnode = models.BigIntegerField()
    tnode = models.BigIntegerField()
    length = models.FloatField()
    roadsegid = models.BigIntegerField(unique=True, primary_key=True)
    postid = models.CharField(max_length=20)
    postdate = models.DateField()
    roadid = models.BigIntegerField()
    rightway = models.IntegerField()
    addsegdt = models.DateField(blank=True, null=True)
    segstat = models.CharField(max_length=1, blank=True, null=True)
    dedstat = models.CharField(max_length=1, blank=True, null=True)
    funclass = models.CharField(max_length=1)
    oneway = models.CharField(max_length=1, blank=True, null=True)
    subdivid = models.BigIntegerField()
    segclass = models.CharField(max_length=1)
    ljurisdic = models.CharField(max_length=2, blank=True, null=True)
    llowaddr = models.BigIntegerField()
    lhighaddr = models.BigIntegerField()
    rjurisdic = models.CharField(max_length=2, blank=True, null=True)
    rlowaddr = models.BigIntegerField()
    rhighaddr = models.BigIntegerField()
    lmixaddr = models.CharField(max_length=1, blank=True, null=True)
    rmixaddr = models.CharField(max_length=1, blank=True, null=True)
    pending = models.CharField(max_length=1, blank=True, null=True)
    abloaddr = models.BigIntegerField()
    abhiaddr = models.BigIntegerField()
    nad83n = models.FloatField()
    nad83e = models.FloatField()
    speed = models.IntegerField()
    l_zip = models.BigIntegerField()
    r_zip = models.BigIntegerField()
    lpsjur = models.CharField(max_length=2, blank=True, null=True)
    rpsjur = models.CharField(max_length=2, blank=True, null=True)
    carto = models.CharField(max_length=1)
    obmh = models.CharField(max_length=1, blank=True, null=True)
    firedriv = models.CharField(max_length=1, blank=True, null=True)
    l_block = models.BigIntegerField()
    r_block = models.BigIntegerField()
    l_tract = models.BigIntegerField()
    r_tract = models.BigIntegerField()
    l_beat = models.IntegerField()
    r_beat = models.IntegerField()
    frxcoord = models.FloatField()
    frycoord = models.FloatField()
    midxcoord = models.FloatField()
    midycoord = models.FloatField()
    toxcoord = models.FloatField()
    toycoord = models.FloatField()
    f_level = models.IntegerField()
    t_level = models.IntegerField()
    l_psblock = models.BigIntegerField()
    r_psblock = models.BigIntegerField()
    rd20pred = models.CharField(max_length=1, blank=True, null=True)
    rd20name = models.CharField(max_length=20)
    rd20sfx = models.CharField(max_length=2, blank=True, null=True)
    rd20full = models.CharField(max_length=25)
    rd30pred = models.CharField(max_length=2, blank=True, null=True)
    rd30name = models.CharField(max_length=30)
    rd30sfx = models.CharField(max_length=4, blank=True, null=True)
    rd30postd = models.CharField(max_length=2, blank=True, null=True)
    rd30full = models.CharField(max_length=41)
    shape_stle = models.FloatField()
    geom = models.MultiLineStringField(srid=4326)

    funclass_dict = {
        "1": "Freeway to freeway ramp",
        "2": "Light (2-lane) collector street",
        "3": "Rural collector road",
        "4": "Major road/4-lane major road",
        "5": "Rural light collector/local road",
        "6": "Prime (primary) arterial",
        "7": "Private street",
        "8": "Recreational parkway",
        "9": "Rural mountain road",
        "A": "Alley",
        "B": "Class I bicycle path",
        "C": "Collector/4-lane collector street",
        "D": "Two-lane major street",
        "E": "Expressway",
        "F": "Freeway",
        "L": "Local street/cul-de-sac",
        "M": "Military street within base",
        "P": "Paper street",
        "Q": "Undocumented",
        "R": "Freeway/expressway on/off ramp",
        "S": "Six-lane major street",
        "T": "Transitway",
        "U": "Unpaved road",
        "W": "Pedestrianway/bikeway",
    }

    segclass_dict = {
        "1": "Freeway/Expressway",
        "2": "Highway/State Routes",
        "3": "Minor Highway/Major Roads",
        "4": "Arterial or Collector",
        "5": "Local Street",
        "6": "Unpaved Road",
        "7": "Private Road",
        "8": "Freeway Transition Ramp",
        "9": "Freeway On/Off Ramp",
        "A": "Alley",
        "H": "Speed Hump",
        "M": "Military Street within Base",
        "P": "Paper Street",
        "Q": "Undocumented",
        "W": "Walkway",
        "Z": "Named Private Street",
    }

    @property
    def funclass_decoded(self) -> str:
        return self.funclass_dict.get(self.funclass, "Unknown")

    @property
    def segclass_decoded(self) -> str:
        return self.segclass_dict.get(self.segclass, "Unknown")

    # Meta class for Roads model
    class Meta:
        indexes = [
            # index for looking up a road segment given a parcel address:
            models.Index(fields=["rd30pred", "rd30name", "rd30sfx", "abloaddr", "abhiaddr"]),
        ]


class TransitPriorityArea(models.Model):
    name = models.CharField(max_length=30)
    shape_star = models.FloatField()
    shape_stle = models.FloatField()
    geom = models.MultiPolygonField(srid=4326)


class HousingSolutionArea(models.Model):
    tier = models.CharField(max_length=10)
    allowance = models.CharField(max_length=150)
    geom = models.MultiPolygonField(srid=4326)


# Map labels
# Based on avoiding generic foreign keys: https://lukeplant.me.uk/blog/posts/avoid-django-genericforeignkey/
class MapLabel(models.Model):
    text = models.CharField(max_length=20)
    geom = models.PointField()

    class Meta:
        abstract = True


class ZoningMapLabel(MapLabel):
    model = models.OneToOneField(ZoningBase, on_delete=models.CASCADE)


class TpaMapLabel(MapLabel):
    model = models.OneToOneField(TransitPriorityArea, on_delete=models.CASCADE)
