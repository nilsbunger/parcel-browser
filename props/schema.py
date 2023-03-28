from ninja import ModelSchema, Schema


class PropertyProfileIn(ModelSchema):
    class Config:
        from props.models import PropertyProfile

        model = PropertyProfile
        model_fields = ["id", "address"]


class PropertyProfileOut(ModelSchema):
    class Config:
        from props.models import PropertyProfile

        model = PropertyProfile
        model_fields = ["id", "address", "legal_entity"]
