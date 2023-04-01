from ninja import ModelSchema


class StdAddressOut(ModelSchema):
    class Config:
        from facts.models import StdAddress

        model = StdAddress
        model_fields = ["id", "street_addr", "city", "state", "zip", "address_features"]


class PropertyProfileOut(ModelSchema):
    address: StdAddressOut

    class Config:
        from props.models import PropertyProfile

        model = PropertyProfile
        model_fields = ["id", "address", "legal_entity"]
