from enum import Enum, EnumMeta

import openai
import polars as pl
import tiktoken
from elt.lib.attom_data import AttomDataApi
from elt.lib.attom_data_struct import AttomPropertyRecord
from elt.lib.rentometer_data import RentometerApi
from facts.models import StdAddress
from lib.mgmt_lib import Home3Command
from parsnip.settings import env
from world.models import Parcel

ATTOM_API_KEY = env("ATTOM_DATA_API_KEY")  # noqa: N806

attom_api = AttomDataApi(api_key=ATTOM_API_KEY)
rentometer_api = RentometerApi(api_key=env("RENTOMETER_API_KEY"))

pl.Config.set_tbl_width_chars(170)  # full-width console


class PropCmdEnum(Enum):
    valuation = "valuation"
    gpt = "gpt"


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


def create_valuation_cmd(subject_property: AttomPropertyRecord):
    rents_dict = get_rents(  # noqa: F841
        {"lat": subject_property.location.latitude, "long": subject_property.location.longitude}
    )

    # get comps for subject property
    comp_response = attom_api.get_comps(subject_property.identifier.apn, "Los Angeles", "CA")
    comp_list = comp_response.group.resp.resp_data.property_info_response.subject_property.properties
    subj_property_from_comp_response = comp_list[0]  # noqa: F841
    subj_prop_df = pl.DataFrame(flatten_dict(subject_property.dict()))
    subj_prop_df = subj_prop_df.with_columns(pl.DataFrame(rents_dict))
    comps = [x.comp_prop for x in comp_list[1:]]

    # Flatten comps to avoid nested dicts
    flat_list = [flatten_dict(comp.dict()) for comp in comps]

    # Convert the flattened comps to a Polars Dataframe
    comps_df = pl.DataFrame(flat_list)

    # add rents for 0BR - 2BR to dataframe
    comps_df = comps_df.with_columns(pl.struct(["lat", "long"]).apply(get_rents).alias("foo")).unnest("foo")

    print(comps_df)
    print("DONE with value function. Printed comps")
    return subj_prop_df, comps_df


def gptgen_cmd(subject_property: AttomPropertyRecord):
    subj_df, comps_df = create_valuation_cmd(subject_property)
    subj_useful_cols = {
        "address.line1": "Street address",
        "summary.yearBuilt": "Year built",
        "sale.saleTransDate": "Last sale date",
        "sale.calculation.pricePerBed": "Price per bedroom",
        "sale.calculation.pricePerSizeUnit": "Price per sqft",
        "sale.amount.saleAmt": "Sale price",
        "building.size.bldgSize": "Building size",
        "building.size.livingSize": "Living area sqft",
        "building.size.universalSize": "Universal size",
        "building.rooms.bathsTotal": "Bathrooms",
        "building.rooms.beds": "Bedrooms",
        "building.summary.unitsCount": "Living unit count",
        "0.median": "Studio median rent",
        "0.percentile_25": "Studio 25th percentile rent",
        "0.percentile_75": "Studio 75th percentile rent",
        "1.median": "1BR median rent",
        "1.percentile_25": "1BR 25th percentile rent",
        "1.percentile_75": "1BR 75th percentile rent",
        "2.median": "2BR median rent",
        "2.percentile_25": "2BR 25th percentile rent",
        "2.percentile_75": "2BR 75th percentile rent",
    }
    comps_useful_cols = {
        "distance_from_subj": "Miles from subject property",
        "street_addr": "Street address",
        "sales_history.price_per_sqft": "Price per sqft",
        "sales_history.loans.loans.0.amount": "Mortgage amount",
        "sales_history.TransferDate_ext": "Last sale date",
        "structure.bath_count": "Bathrooms count",
        "structure.br_count": "Bedrooms count",
        "structure.living_unit_count": "Living unit count",
        "structure.living_area_sqft": "Living area sqft",
        "structure.structure_analysis.year_built": "Year built",
        "site.lot_sq_ft": "Lot sqft",
        "tax.assessed_val": "Tax assessed value",
        "0.median": "Studio median rent",
        "0.percentile_25": "Studio 25th percentile rent",
        "0.percentile_75": "Studio 75th percentile rent",
        "1.median": "1BR median rent",
        "1.percentile_25": "1BR 25th percentile rent",
        "1.percentile_75": "1BR 75th percentile rent",
        "2.median": "2BR median rent",
        "2.percentile_25": "2BR 25th percentile rent",
        "2.percentile_75": "2BR 75th percentile rent",
    }
    subj_useful_df = subj_df.select(subj_useful_cols.keys()).rename(subj_useful_cols)
    comps_useful_df = comps_df.select(comps_useful_cols.keys()).rename(comps_useful_cols)

    subj_useful_df = subj_useful_df.with_columns(
        pl.col("Price per sqft").cast(pl.Int64, strict=False),
        pl.col("Price per bedroom").cast(pl.Int64, strict=False),
    )
    comps_useful_df = comps_useful_df.with_columns(
        pl.col("Price per sqft").cast(pl.Int64, strict=False),
        pl.col("Lot sqft").cast(pl.Int64, strict=False),
        pl.col("Miles from subject property").round(1),
    )
    subj_prompt = "".join([f"{k}: {v}\n" for k, v in subj_useful_df.to_dicts()[0].items()])
    comp_prompt = ""
    for comp in comps_useful_df.to_dicts()[0:5]:
        comp_prompt += "\n\nRecent sale:\n"
        comp_prompt += "".join([f"{k}: {v}\n" for k, v in comp.items()])

    system_prompt = f"""You're a multilisting apartment real estate broker named Taylor Avakian based in Los Angeles.

Here's your bio:'
Taylor Avakian is a premier client advisor for the acquisition and disposition of multifamily assets nationwide.
His primary focus is on advancing his client’s positions by observing market trends and capitalizing on opportunities.
Taylor has worked on countless transactions, both as an advisor and a principal. He is adept at managing the process
from beginning to end, including due diligence, financing, marketing, and sales. Taylor’s extensive knowledge of
the market and his ability to identify opportunities are what make him stand out from other agents. He has been
recognized as one of his region’s top commercial real estate agents, serving clients from all over the United States.
His clients include some of the most notable companies in the world, and he prides himself on providing them with
exceptional service.

Most agents take a two-pronged approach. Taylor takes a different stance. His unique perspective allows him to
identify opportunities that most agents would miss, setting him apart from the rest of the industry. He is not only
able to help his clients make smart investments, but he also helps them avoid costly mistakes.

When he is not in the office, Taylor enjoys working out, listening to podcasts, being outdoors, and spending time
with friends and family (specifically with food involved).

Prior to his current role at Matthews™, Taylor founded a nutritional supplement company. His market insights and
incredible business savviness allowed the company to grow 7000% over a two-year period. After the company was
acquired, Taylor shifted his focus to growing real estate portfolios, where he now pursues the goal of maximizing
clients returns. B.S., Finance and Real Estate, University of Alabama'

You're reaching out to property owners who might be interested in selling. Typically, they are more likely to sell if
they're older, they've held the property a long time, or if they don't realize their property is worth a lot now. You're
looking for properties that have 10-50 units.

The user will give you a subject property that is a potential target, along with useful information about it,
and a list of several recent nearby property sales, along with more information about those.

You'll write an email to the property owner of the subject property, introducing yourself, giving them some a few useful
insights about the property and comparable properties. Invite them to contact you at 565-345-2345 to discuss
maximizing the value of their property or potentially selling it. The email should be persuasive and
professional.
"""

    user_prompt = f"""
Here's a subject property as a potential target and relevant information about it:
{subj_prompt}

Here are 4 comparable properties with recent sales, and relevant information about them:
{comp_prompt}

"""
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(system_prompt + user_prompt)
    print(f"{len(tokens)} tokens required")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    openai.api_key = env("OPENAI_API_KEY")
    result = openai.ChatCompletion.create(messages=messages, model="gpt-3.5-turbo", temperature=0.4)  # noqa:F841

    print("DONE")


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
            result = input(f"[+]:Choose a command: {','.join(enum_cls.__members__.keys())}")

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

        # TODO: Temporary hardcode
        # cmd = self.choose_cmd(PropCmdEnum)
        cmd = PropCmdEnum.gpt
        if cmd is PropCmdEnum.valuation:
            create_valuation_cmd(subject_property)
        elif cmd is PropCmdEnum.gpt:
            gptgen_cmd(subject_property)
        else:
            raise Exception("Unknown command")
