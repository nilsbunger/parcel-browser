# Register your models here.
from django.contrib.admin import EmptyFieldListFilter, SimpleListFilter
from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.db.models import Count, Prefetch
from django.utils.html import format_html
from more_itertools import collapse

from elt.admin_utils import InlineRenderedAdminMixin
from elt.home3_admin import Home3Admin
from elt.models import (
    ExternalApiData,
    RawCaliResourceLevel,
    RawSfHeTableA,
    RawSfHeTableB,
    RawSfHeTableC,
    RawSfParcel,
    RawSfParcelWrap,
    RawSfRentboardHousingInv,
    RawSfReportall,
    RawSfZoning,
    RawSfZoningHeightBulk,
)
from elt.widgets import JSONEditorWidget


# Registering models: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#modeladmin-objects
class RawSfParcelWrapInline(admin.StackedInline):
    model = RawSfParcelWrap
    extra = 0
    fields = ("parcel_wrap_link",)
    readonly_fields = ("parcel_wrap_link",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def parcel_wrap_link(self, obj):
        """Provide a link to the detail view of the inline object."""
        url = obj.get_admin_url()  # Get admin URL
        return format_html('<a href="{}">{}</a>', url, obj.apn)

    parcel_wrap_link.short_description = "Parcel Wrap"


@admin.register(RawSfParcel)
class RawSfParcelAdmin(Home3Admin):
    related_gis_models = [RawSfZoning, RawSfZoningHeightBulk]
    related_apn_models = [RawSfHeTableA, RawSfHeTableB]
    # what to show in list view:
    list_display = ["blklot", "resolved_address", "zoning_cod", "zoning_dis"]  # "show_detail"]
    # fmt:off
    _fieldlist = ['resolved_address', 'geom', ('blklot', 'block_num', 'mapblklot', 'lot_num', 'odd_even'),
                  ('zoning_cod', 'zoning_dis'), ('from_addre', 'to_address', 'street_nam', 'street_typ',),
                  ('in_asr_sec', 'pw_recorde', 'active',), ('date_rec_a', 'date_rec_d'),
                  ('date_map_a', 'date_map_d', 'date_map_2'), ('project_id', 'project_2', 'project_3')]
    # fmt:on
    # what to show in detail view:
    fields = list(_fieldlist)
    readonly_fields = list(collapse(set(_fieldlist) - {"geom"}))
    search_fields = ["mapblklot", "blklot", "street_nam", "from_addre", "zoning_cod"]
    inlines = [RawSfParcelWrapInline]


class RawSfRentboardHousingInvInline(admin.TabularInline):
    model = RawSfRentboardHousingInv
    extra = 0
    fields = (
        "unit_number",
        "bedroom_count",
        "bathroom_count",
        "monthly_rent",
        "year",
        "occupancy_type",
        "view_detail",
    )
    readonly_fields = ("view_detail",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def view_detail(self, obj):
        """Provide a link to the detail view of the inline object."""
        url = obj.get_admin_url()  # Get admin URL
        return format_html('<a href="{}">View</a>', url)

    view_detail.short_description = "View Detail"


class RentCountFilter(SimpleListFilter):
    title = "rent_count"
    parameter_name = "rent_count"

    def lookups(self, request, model_admin):
        return [
            ("0", "0"),
            ("1", "1 or more"),
            ("2", "2 or more"),
            ("5", "5 or more"),
            ("10", "10 or more"),
            ("20", "20 or more"),
            ("50", "50 or more"),
            ("100", "100 or more"),
            ("200", "200 or more"),
        ]

    def queryset(self, request, queryset):
        # cats = A.objects.annotate(num_b=Count('b')).filter(num_b__lt=2)
        if self.value() is None:
            return queryset
        val = int(self.value())
        if val == 0:
            return queryset.annotate(num=Count("rawsfrentboardhousinginv")).filter(num=0)
        else:
            return queryset.annotate(num=Count("rawsfrentboardhousinginv")).filter(num__gte=val)


@admin.register(RawSfParcelWrap)
class RawSfParcelWrapAdmin(Home3Admin):
    model = RawSfParcelWrap
    fields = ["apn", "rent_count", ("parcel", "he_table_a", "he_table_b", "reportall_parcel")]
    list_display = ["apn", "rent_count", "parcel", "he_table_a", "he_table_b", "reportall_parcel"]
    readonly_fields = ["apn", "rent_count", "parcel", "he_table_a", "he_table_b", "reportall_parcel"]

    search_fields = ["apn", "parcel__street_nam", "parcel__from_addre", "parcel__zoning_cod", "parcel__street_typ"]
    extra_inline_fields = ["parcel", "he_table_a", "he_table_b", "reportall_parcel"]
    inlines = [RawSfRentboardHousingInvInline]
    list_filter = [
        ("parcel", EmptyFieldListFilter),
        ("he_table_a", EmptyFieldListFilter),
        ("he_table_b", EmptyFieldListFilter),
        ("reportall_parcel", EmptyFieldListFilter),
        RentCountFilter,
    ]

    def get_queryset(self, request):
        """Queryset for the list view, prefetching related data for list view.
        By default this would be
        """
        qs = super().get_queryset(request)
        if getattr(request, "list_view", False):
            # We're in the list view, so be careful about fetching data.

            qs = (
                qs.select_related("parcel", "he_table_a", "he_table_b", "reportall_parcel")
                .prefetch_related(
                    Prefetch("rawsfrentboardhousinginv_set", queryset=RawSfRentboardHousingInv.objects.all())
                )
                .only(
                    "apn", "parcel__blklot", "he_table_a__mapblklot", "he_table_b__mapblklot", "reportall_parcel_id"
                )
            )
            # .prefetch_related("rawsfrentboardhousinginv_set")
        else:
            # we're not in list view (eg in change view), so fetch all data.
            qs = qs.select_related("parcel", "he_table_a", "he_table_b", "reportall_parcel")
        return qs

    def rent_count(self, obj):
        return obj.rawsfrentboardhousinginv_set.count()

    rent_count.short_description = "# rent reports"


@admin.register(RawSfZoning)
class RawSfZoningAdmin(InlineRenderedAdminMixin, Home3Admin):
    list_display = ["codesection", "districtname", "gen", "url", "zoning", "zoning_sim"]
    fields = (("zoning", "zoning_sim"), ("codesection", "districtname"), ("gen", "url"), "geom")
    readonly_fields = ("codesection", "districtname", "gen", "url", "zoning", "zoning_sim")


@admin.register(RawSfZoningHeightBulk)
class RawSfZoningHeightBulkAdmin(InlineRenderedAdminMixin, Home3Admin):
    list_display = ["gen_height", "height"]
    fields = ["gen_height", "height", "geom"]
    readonly_fields = ["gen_height", "height"]
    search_fields = ["gen_height", "height"]


@admin.register(RawSfHeTableA)
class RawSfHeTableAAdmin(InlineRenderedAdminMixin, Home3Admin):
    model = RawSfHeTableA
    list_display = ["mapblklot", "address", "ex_gp_des", "ex_zoning", "acres", "ex_use_vac", "run_date"]
    search_fields = ["mapblklot", "address", "ex_gp_des", "ex_zoning"]
    list_filter = ["ex_zoning"]

    # fmt:off
    _fieldlist = [
        ("address", "mapblklot", "acres"),
        ("ex_gp_des", "ex_zoning", "ex_use_vac"),
        ("min_dens", "max_dens", "infra"),
        ("public", "site_stat", "id_last2", "li"),
        ("mod", "amod", "capacity", "con_sites",),
        ("opt1", "opt2", "zip5", "run_date",)
    ]
    # fmt:on
    fields = _fieldlist
    readonly_fields = list(collapse(_fieldlist))
    inlines = [RawSfParcelWrapInline]


@admin.register(RawSfHeTableB)
class RawSfHeTableBAdmin(InlineRenderedAdminMixin, Home3Admin):
    model = RawSfHeTableB
    # fmt:off
    list_display = ["mapblklot", "address", "acres", "ex_zoning", "m1_zoning", "m2_zoning", "m3_zoning", "vacant",
                    "ex_use", "run_date"]
    # fmt:on
    list_filter = ["vacant", "ex_zoning", "m1_zoning", "m2_zoning", "m3_zoning", "run_date"]
    search_fields = ["mapblklot", "address"]

    # fmt:off
    _fieldlist = [
        ('address', 'mapblklot', 'acres',),
        ('ex_use', 'ex_gp_type', 'ex_zoning',),
        ('m1_gp_type', 'm1_zoning', 'm1_maxdens', 'm1_cap',),
        ('m2_gp_type', 'm2_zoning', 'm2_maxdens', 'm2_cap',),
        ('m3_gp_type', 'm3_zoning', 'm3_maxdens', 'm3_cap',),
        ('m1_vli', 'm1_li', 'm1_m', 'm1_am',),
        ('m2_vli', 'm2_li', 'm2_m', 'm2_am',),
        ('m3_vli', 'm3_li', 'm3_m', 'm3_am',),
        ('shortfall', 'min_dens', 'vacant', 'infra',),
        ('ss_map1', 'ss_map2', 'ss_map3',),
        ('zip5', 'run_date',),
    ]
    # fmt:on
    fields = _fieldlist
    readonly_fields = list(collapse(_fieldlist))


@admin.register(RawSfHeTableC)
class RawSfHeTableCAdmin(Home3Admin):
    model = RawSfHeTableC
    list_display = ["zoning", "zoning_name", "zoning_type", "residential_uses_allowed", "run_date"]
    search_fields = ["zoning", "zoning_name", "zoning_type", "residential_uses_allowed"]


@admin.register(RawSfReportall)
class RawSfReportallAdmin(Home3Admin):
    model = RawSfReportall
    # fmt:off
    _fieldlist = [
        ("situs", "parcel_id", "acreage", "calc_acrea"),
        "geom",
        ("owner", "owner_occ",),
        ("land_use_class", "land_us_01"),
        ("bldg_sqft", "buildings", "bedrooms", "fullbath", "halfbath", "total_bath", "total_room"),
        ("year_built", "story_height", "style", "eff_year_b"),
        ("condition", "exterior", "cooling", "heatsrc"),
        ("mkt_val_bldg", "mkt_val_land", "mkt_val_total", "sale_price", "trans_date"),
        ("m_recpnt", "m_addressn", "m_streetnm", "m_streetpd", "m_streetpo", "m_streetpr"),
        ("m_statenm", "m_country", "m_placenm"),
        ("m_subocc", "m_uspsbox", "m_zipcode"),
        ("mail_name", "mail_address", "mail_ad_01", "mail_ad_02"),
        ("muni_name", "state_abbr", "school_dis"),
        ("situs_city", "situs_zip", "situs_zip4", "zip_code"),
        ("usps_resid", "routing_nu"),
        ("zoning", "zone_subty"),
        ("latitude", "longitude", "elevation"),
        ("water", "sewer", "fld_zone",),
        ("legal_desc", "legal_d_01", "legal_d_02"),
        ("alt_id_1", "alt_id_2"),
        ("map_book", "map_page", "ngh_code"),
        ("census_pla", "county_fip", "county_nam", "cty_row_id"),
        ("addr_number", "addr_se_01", "addr_sec_u", "addr_st_01", "addr_st_02", "addr_st_03", "addr_street"),
        ("robust_id", "last_updat", "run_date")
    ]
    # fmt:on
    fields = list(_fieldlist)
    readonly_fields = list(collapse(set(_fieldlist) - {"geom"}))
    field_options = {
        "latitude": {"sig_figs": 7},
        "longitude": {"sig_figs": 7},
    }


@admin.register(RawCaliResourceLevel)
class RawCaliResourceLevelAdmin(Home3Admin):
    model = RawCaliResourceLevel
    list_display = ["cnty_nm", "region", "oppcat"]

    search_fields = ["cnty_nm", "region", "oppcat"]
    # fmt:off
    readonly_fields = [
        "cnty_nm", "countyd", "ecn_dmn", "ed_domn", "env_hl_field", "fips", "fips_bg", "index", "oppcat",
        "region", "run_date"
    ]
    # fmt:on


@admin.register(ExternalApiData)
class ExternalApiDataAdmin(admin.ModelAdmin):
    change_form_template = "elt/admin/home3_admin_change_form.html"
    model = ExternalApiData
    list_display = ["vendor", "created_at", "lookup_key", "hash_version"]
    list_filter = ["vendor", "created_at", "lookup_key", "hash_version"]
    readonly_fields = ["vendor", "created_at", "lookup_hash", "lookup_key", "hash_version"]
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }


@admin.register(RawSfRentboardHousingInv)
class RawSfRentBoardHousingInvAdmin(Home3Admin):
    model = RawSfRentboardHousingInv
    list_display = ["parcel_number", "unit_address", "unit_number", "monthly_rent", "email", "rawsfparcelwrap"]
    search_fields = ["parcel_numer", "unit_address", "email"]
    # fields = ["rawsfparcelwrap"]
    readonly_fields = [
        "rawsfparcelwrap",
        "parcel_number",
        "case_type_name",
        "unit_number",
        "unit_address",
        "occupancy_type",
        "bedroom_count",
        "bathroom_count",
        "square_footage",
        "monthly_rent",
        "base_rentinclude_utility",
        "day",
        "month",
        "year",
        "past_occupancy",
        "contact_association",
        "first_name",
        "last_name",
        "email",
        "phone",
        "vacancy_date",
        "contact_type",
        "signature_date2",
        "signature_date1",
        "occupancy_or_vacancy",
        "run_date",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("rawsfparcelwrap")
        return qs
