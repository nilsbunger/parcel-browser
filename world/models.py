from django.contrib.postgres.fields import ArrayField

# Create your models here.

# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models


class AnalyzedParcel(models.Model):
    apn = models.CharField(max_length=10, blank=True, null=True, unique=True)
    lot_size = models.IntegerField(blank=True, null=True)
    building_size = models.IntegerField(blank=True, null=True)
    skip = models.BooleanField(blank=True, null=True)
    skip_reason = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['apn'])
        ]


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


# This is an auto-generated Django model module created by ogrinspect.

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

    def __str__(self):
        if self.acreage > 0:
            lot_str = "%s acres" % self.acreage
        else:
            lot_str = "%s lot" % self.usable_sq_field
        base_str = '%s %s %s %s: %s living, ' % (
            self.apn, self.situs_addr, self.situs_stre, self.situs_zip, self.total_lvg_field)
        return base_str + lot_str

    class Meta:
        indexes = [
            models.Index(fields=['apn']),
            models.Index(fields=['situs_addr'])
        ]


class ParcelSlope(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field='apn')
    grade = models.IntegerField()
    polys = models.MultiPolygonField(blank=True, null=True)
    run_date = models.DateField(auto_now=True)  # note: only updated on model.save

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['parcel', 'grade'], name='unique_parcel_grade_bucket'),
        ]


class Marker(models.Model):
    """A marker with name and location."""

    name = models.CharField(max_length=255)
    location = models.PointField()

    def __str__(self):
        """Return string representation."""
        return self.name


class WorldBorder(models.Model):
    # Regular Django fields corresponding to the attributes in the
    # world borders shapefile.
    name = models.CharField(max_length=50)
    area = models.IntegerField()
    pop2005 = models.IntegerField('Population 2005')
    fips = models.CharField('FIPS Code', max_length=2, null=True)
    iso2 = models.CharField('2 Digit ISO', max_length=2)
    iso3 = models.CharField('3 Digit ISO', max_length=3)
    un = models.IntegerField('United Nations Code')
    region = models.IntegerField('Region Code')
    subregion = models.IntegerField('Sub-Region Code')
    lon = models.FloatField()
    lat = models.FloatField()

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name


class TopographyLoads(models.Model):
    fname = models.CharField('filename', max_length=200)
    extents = models.PolygonField(srid=4326, unique=True)
    run_date = models.DateField(auto_now=True)  # note: only updated on model.save


class Topography(models.Model):  # model based on Topo_2014_2Ft_PowayLaMesa data set.
    elev = models.FloatField()
    ltype = models.IntegerField()
    index_field = models.IntegerField()
    shape_length = models.FloatField()
    geom = models.MultiLineStringField(srid=4326)


class ParcelScenario(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)

    git_commit_hash = models.CharField(max_length=40)
    date_time_ran = models.DateTimeField(auto_now_add=True)
    input_parameters = models.JSONField()

    # Added buildings (existing buildings stored as BuildingOnScenario)
    placed_buildings = ArrayField(
        base_field=models.MultiPolygonField(srid=4326))

    # Other geometries
    setback_front_geom = models.MultiPolygonField(
        srid=4326, blank=True, null=True)
    setback_side_geom = models.MultiPolygonField(
        srid=4326, blank=True, null=True)
    setback_rear_geom = models.MultiPolygonField(
        srid=4326, blank=True, null=True)
    buffered_buidings_geom = models.MultiPolygonField(
        srid=4326, blank=True, null=True)
    topography_nobuild_geom = models.MultiPolygonField(
        srid=4326, blank=True, null=True)
    avail_geom = models.MultiPolygonField(srid=4326, blank=True, null=True)

    parcel_area = models.FloatField()  # In square meters
    area_added = models.FloatField()  # In square meters

    # Financial modelling details
    # Score info

    logs = models.CharField(blank=True, max_length=10000)
    comments = models.CharField(blank=True, max_length=10000)


class BuildingOnScenario(models.Model):
    # Model is used for storing a building on a scenario. These are existing buildings
    # Note: Eventually, we should add support for ADUs that are converted from
    # existing buildings, e.g. garages
    class BuildingType(models.TextChoices):
        MAIN = 'MAIN'
        ACCESSSORY = 'ACCESSORY'
        ENCROACHMENT = 'ENCROACHMENT'

    building = models.ForeignKey(
        BuildingOutlines, on_delete=models.CASCADE)
    scenario = models.ForeignKey(ParcelScenario, on_delete=models.CASCADE)
    type = models.CharField(max_length=15, choices=BuildingType.choices)


class Roads(models.Model):
    fnode = models.BigIntegerField()
    tnode = models.BigIntegerField()
    length = models.FloatField()
    roadsegid = models.BigIntegerField()
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


class PropertyListing(models.Model):
    class ListingStatus(models.TextChoices):
        ACTIVE = 'ACTIVE'
        PENDING = 'PENDING'
        SOLD = 'SOLD'
        MISSING = 'MISSING'
        WITHDRAWN = 'WITHDRAWN'
        OFFMARKET = 'OFFMARKET'

    price = models.IntegerField(blank=True, null=True)
    addr = models.CharField(max_length=80)  # street number and name
    zipcode = models.IntegerField(blank=True, null=True)
    br = models.IntegerField()
    ba = models.IntegerField()
    founddate = models.DateTimeField(auto_now_add=True)
    seendate = models.DateTimeField(auto_now=True)  # when last seen (date of sale when sold)
    mlsid = models.CharField(max_length=20)
    size = models.IntegerField()  # living area size in sq ft.
    thumbnail = models.CharField(max_length=200)
    listing_url = models.CharField(max_length=100)
    soldprice = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=ListingStatus.choices)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field='apn', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['zipcode'])
        ]


world_mapping = {
    'fips': 'FIPS',
    'iso2': 'ISO2',
    'iso3': 'ISO3',
    'un': 'UN',
    'name': 'NAME',
    'area': 'AREA',
    'pop2005': 'POP2005',
    'region': 'REGION',
    'subregion': 'SUBREGION',
    'lon': 'LON',
    'lat': 'LAT',
    'mpoly': 'MULTIPOLYGON',
}

# Auto-generated `LayerMapping` dictionary for ZoningBase model
zoningbase_mapping = {
    'zone_name': 'ZONE_NAME',
    'imp_date': 'IMP_DATE',
    'ordnum': 'ORDNUM',
    'shape_star': 'Shape_STAr',
    'shape_stle': 'Shape_STLe',
    'geom': 'MULTIPOLYGON',
}

# Auto-generated `LayerMapping` dictionary for Parcel model
parcel_mapping = {
    'apn': 'APN',
    'apn_8': 'APN_8',
    'parcelid': 'PARCELID',
    'own_name1': 'OWN_NAME1',
    'own_name2': 'OWN_NAME2',
    'own_name3': 'OWN_NAME3',
    'fractint': 'FRACTINT',
    'own_addr1': 'OWN_ADDR1',
    'own_addr2': 'OWN_ADDR2',
    'own_addr3': 'OWN_ADDR3',
    'own_addr4': 'OWN_ADDR4',
    'own_zip': 'OWN_ZIP',
    'situs_juri': 'SITUS_JURI',
    'situs_stre': 'SITUS_STRE',
    'situs_suff': 'SITUS_SUFF',
    'situs_post': 'SITUS_POST',
    'situs_pre_field': 'SITUS_PRE_',
    'situs_addr': 'SITUS_ADDR',
    'situs_frac': 'SITUS_FRAC',
    'situs_buil': 'SITUS_BUIL',
    'situs_suit': 'SITUS_SUIT',
    'legldesc': 'LEGLDESC',
    'asr_land': 'ASR_LAND',
    'asr_impr': 'ASR_IMPR',
    'asr_total': 'ASR_TOTAL',
    'doctype': 'DOCTYPE',
    'docnmbr': 'DOCNMBR',
    'docdate': 'DOCDATE',
    'acreage': 'ACREAGE',
    'taxstat': 'TAXSTAT',
    'ownerocc': 'OWNEROCC',
    'tranum': 'TRANUM',
    'asr_zone': 'ASR_ZONE',
    'asr_landus': 'ASR_LANDUS',
    'unitqty': 'UNITQTY',
    'submap': 'SUBMAP',
    'subname': 'SUBNAME',
    'nucleus_zo': 'NUCLEUS_ZO',
    'nucleus_us': 'NUCLEUS_US',
    'situs_comm': 'SITUS_COMM',
    'year_effec': 'YEAR_EFFEC',
    'total_lvg_field': 'TOTAL_LVG_',
    'bedrooms': 'BEDROOMS',
    'baths': 'BATHS',
    'addition_a': 'ADDITION_A',
    'garage_con': 'GARAGE_CON',
    'garage_sta': 'GARAGE_STA',
    'carport_st': 'CARPORT_ST',
    'pool': 'POOL',
    'par_view': 'PAR_VIEW',
    'usable_sq_field': 'USABLE_SQ_',
    'qual_class': 'QUAL_CLASS',
    'nucleus_si': 'NUCLEUS_SI',
    'nucleus_1': 'NUCLEUS__1',
    'nucleus_2': 'NUCLEUS__2',
    'situs_zip': 'SITUS_ZIP',
    'x_coord': 'x_coord',
    'y_coord': 'y_coord',
    'overlay_ju': 'overlay_ju',
    'sub_type': 'sub_type',
    'multi': 'multi',
    'shape_star': 'SHAPE_STAr',
    'shape_stle': 'SHAPE_STLe',
    'geom': 'MULTIPOLYGON',
}

buildingoutlines_mapping = {
    'outline_id': 'outline_id',
    'bldgid': 'bldgID',
    'centroid_x': 'CENTROID_X',
    'centroid_y': 'CENTROID_Y',
    'area': 'AREA',
    'comment': 'COMMENT',
    'shape_leng': 'Shape_Leng',
    'shape_star': 'Shape_STAr',
    'shape_stle': 'Shape_STLe',
    'geom': 'MULTIPOLYGON',
}

topography_mapping = {
    'elev': 'ELEV',
    'ltype': 'LTYPE',
    'index_field': 'INDEX_',
    'shape_length': 'Shape_Length',
    'geom': 'MULTILINESTRING',
}

roads_mapping = {
    'fnode': 'FNODE',
    'tnode': 'TNODE',
    'length': 'LENGTH',
    'roadsegid': 'ROADSEGID',
    'postid': 'POSTID',
    'postdate': 'POSTDATE',
    'roadid': 'ROADID',
    'rightway': 'RIGHTWAY',
    'addsegdt': 'ADDSEGDT',
    'segstat': 'SEGSTAT',
    'dedstat': 'DEDSTAT',
    'funclass': 'FUNCLASS',
    'oneway': 'ONEWAY',
    'subdivid': 'SUBDIVID',
    'segclass': 'SEGCLASS',
    'ljurisdic': 'LJURISDIC',
    'llowaddr': 'LLOWADDR',
    'lhighaddr': 'LHIGHADDR',
    'rjurisdic': 'RJURISDIC',
    'rlowaddr': 'RLOWADDR',
    'rhighaddr': 'RHIGHADDR',
    'lmixaddr': 'LMIXADDR',
    'rmixaddr': 'RMIXADDR',
    'pending': 'PENDING',
    'abloaddr': 'ABLOADDR',
    'abhiaddr': 'ABHIADDR',
    'nad83n': 'NAD83N',
    'nad83e': 'NAD83E',
    'speed': 'SPEED',
    'l_zip': 'L_ZIP',
    'r_zip': 'R_ZIP',
    'lpsjur': 'LPSJUR',
    'rpsjur': 'RPSJUR',
    'carto': 'CARTO',
    'obmh': 'OBMH',
    'firedriv': 'FIREDRIV',
    'l_block': 'L_BLOCK',
    'r_block': 'R_BLOCK',
    'l_tract': 'L_TRACT',
    'r_tract': 'R_TRACT',
    'l_beat': 'L_BEAT',
    'r_beat': 'R_BEAT',
    'frxcoord': 'FRXCOORD',
    'frycoord': 'FRYCOORD',
    'midxcoord': 'MIDXCOORD',
    'midycoord': 'MIDYCOORD',
    'toxcoord': 'TOXCOORD',
    'toycoord': 'TOYCOORD',
    'f_level': 'F_LEVEL',
    't_level': 'T_LEVEL',
    'l_psblock': 'L_PSBLOCK',
    'r_psblock': 'R_PSBLOCK',
    'rd20pred': 'RD20PRED',
    'rd20name': 'RD20NAME',
    'rd20sfx': 'RD20SFX',
    'rd20full': 'RD20FULL',
    'rd30pred': 'RD30PRED',
    'rd30name': 'RD30NAME',
    'rd30sfx': 'RD30SFX',
    'rd30postd': 'RD30POSTD',
    'rd30full': 'RD30FULL',
    'shape_stle': 'SHAPE_STLe',
    'geom': 'MULTILINESTRING',
}
