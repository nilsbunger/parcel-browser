from abc import ABCMeta
from typing import Generic, TypeVar, Union

from ninja import ModelSchema, Schema
from pydantic.generics import GenericModel

# Base class for API responses using Django-ninja. In typescript, the apiRequest() parses out these fields.
# TODO: can probably make these mixins to avoid the duplication
# class ApiResponseSchema(Schema, metaclass=ABCMeta):
#     success: bool
#     message: str
#
#
ResponseDataSchema = TypeVar("ResponseDataSchema")


# Generic API response class. Generic ResponseDataSchema can be a django-ninja Schema or a ModelSchema
class ApiResponseSchema(GenericModel, Generic[ResponseDataSchema]):
    errors: bool
    message: str
    data: Union[ResponseDataSchema, None]
