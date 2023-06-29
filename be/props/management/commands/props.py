from enum import Enum, EnumMeta

import polars as pl
from elt.lib.attom_data import AttomDataApi
from elt.lib.attom_data_struct import AttomPropertyRecord
from elt.lib.rentometer_data import RentometerApi
from facts.models import StdAddress
from lib.home3_command import Home3Command
from parsnip.settings import env
from world.models import Parcel

ATTOM_API_KEY = env("ATTOM_DATA_API_KEY")  # noqa: N806

attom_api = AttomDataApi(api_key=ATTOM_API_KEY)
rentometer_api = RentometerApi(api_key=env("RENTOMETER_API_KEY"))


pl.Config.set_tbl_width_chars(170)  # full-width console


class PropCmdEnum(Enum):
    value = "value"
    gptgen = "gptgen"


def flatten_item(item, parent_key="", sep="_"):
    if isinstance(item, dict):
        return flatten_dict(item, parent_key=parent_key, sep=sep)
    elif isinstance(item, list):
        list_items = {}
        for i, v in enumerate(item):
            new_key = f"{parent_key}{sep}{i}"
            flattened_value = flatten_item(v, parent_key=new_key, sep=sep)
            if isinstance(flattened_value, dict):
                list_items.update(flattened_value)
            else:
                list_items[new_key] = flattened_value
        return list_items
    else:
        return item


def flatten_dict(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        flattened_value = flatten_item(v, parent_key=new_key, sep=sep)
        if isinstance(flattened_value, dict):
            items.extend(flattened_value.items())
        else:
            items.append((new_key, flattened_value))
    return dict(items)


def get_rents(cols) -> dict[str, int]:
    # return flattened dict of rent data : mean, median, 25th, 75th, std_dev, samples, for 0br, 1br, 2br
    print("ARGS=", cols)
    lat, long = cols["lat"], cols["long"]
    rent_responses = [rentometer_api.rent_for_location(lat=lat, long=long, br=n, ba=1) for n in range(3)]
    rents = {}
    for r in rent_responses:
        for x in ["median", "percentile_25", "percentile_75", "std_dev", "samples"]:
            rents[f"{r.bedrooms}.{x}"] = getattr(r, x)

    print(rents)
    return rents


def create_valuation(subject_property: AttomPropertyRecord):
    rents_dict = get_rents(  # noqa: F841
        {"lat": subject_property.location.latitude, "long": subject_property.location.longitude}
    )

    # get comps for subject property
    comp_response = attom_api.get_comps(subject_property.identifier.apn, "Los Angeles", "CA")
    comp_list = comp_response.group.resp.resp_data.property_info_response.subject_property.properties
    subj_property_from_comp_response = comp_list[0]  # noqa: F841
    comps = [x.comp_prop for x in comp_list[1:]]

    # Flatten comps to avoid nested dicts
    flat_list = [flatten_dict(comp.dict()) for comp in comps]

    # Convert the flattened comps to a Polars Dataframe
    comps_df = pl.DataFrame(flat_list)

    # add rents for 0BR - 2BR to dataframe
    comps_df = comps_df.with_columns(pl.struct(["lat", "long"]).apply(get_rents).alias("foo")).unnest("foo")

    print(comps_df)

    print("DONE with value function. Printed comps")

    # raise NotImplementedError()


def gptgen(subject_property: AttomPropertyRecord):
    raise NotImplementedError()


class Command(Home3Command):
    help = "Generate valuation for a property."

    def add_arguments(self, parser):
        ...
        # parser.add_argument(
        #     "cmd",
        #     action="store",
        #     choices=PropCmdEnum,
        #     type=PropCmdEnum,
        #     help="Property analysis command to run",
        # )

    def choose_cmd(self, enum_cls: EnumMeta):
        result = ""
        while not hasattr(enum_cls, result):
            result = input(f"[+]:Select the length you want for your key: {','.join(enum_cls.__members__.keys())}")

        print(enum_cls[result])
        return enum_cls[result]

    def handle(self, *args, **options):
        multifam_sd_parcels = Parcel.objects.filter(unitqty__gte=10, unitqty__lte=50)
        print(len(multifam_sd_parcels))

        # get multifam properties in 90006 (LA K-town) zip (shouldbe cached)
        props_in_90006 = attom_api.get_properties_in_zip("90006")
        print(len(props_in_90006.property))
        prop = props_in_90006.property[0]
        profiles = []
        # get detailed profiles for first 10 properties -- these are our test cases.
        for prop in props_in_90006.property[:9]:
            prop_addr = StdAddress.from_attom(prop.address)
            profiles.append(attom_api.get_property_expanded_profile(prop_addr))

        # get subject property -- 2769 SAN MARINO ST, LOS ANGELES, CA 90006
        subject_property = profiles[5]
        assert subject_property.identifier.apn == "5077-028-025"

        cmd = self.choose_cmd(PropCmdEnum)
        if cmd is PropCmdEnum.value:
            create_valuation(subject_property)
        elif cmd is PropCmdEnum.gptgen:
            raise NotImplementedError()
