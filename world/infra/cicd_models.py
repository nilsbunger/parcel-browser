from django.db.models import Model as DjangoModel


class Model(DjangoModel):
    pass


class GeometryField:
    pass


class MultiPolygonField(GeometryField):
    pass


class MultiLineStringField(GeometryField):
    pass


class PointField(GeometryField):
    pass
