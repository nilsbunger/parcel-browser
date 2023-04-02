from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from ninja import ModelSchema, NinjaAPI, Schema
from ninja.security import django_auth
from pydantic import constr

from lib.ninja_api import ApiResponseSchema
from userflows.models import User

# from .api_schema import ProfileSchema

userflows_api = NinjaAPI(
    auth=django_auth, csrf=True, urls_namespace="userflows", docs_decorator=staff_member_required
)


################################################################################################
## User info API
################################################################################################


class LoginSchema(Schema):
    email: str
    password: constr(min_length=8, max_length=32)
    rememberMe: bool = False


class UserSchema(ModelSchema):
    class Config:
        model = User
        model_fields = ["first_name", "last_name", "email"]


class LoginResponseDataSchema(Schema):
    user: UserSchema = None


LoginResponseSchema = ApiResponseSchema[LoginResponseDataSchema]


LogoutResponseSchema = ApiResponseSchema[None]


# Login endpoint: allow unauthenticated access
@userflows_api.post("/login", auth=None, response=LoginResponseSchema)
def _login(request, payload: LoginSchema):
    ...
    # TODO: better validation and rate-limiting here to prevent bad login attempts. See what django-allauth did?
    # TODO: support returning form errors (should be part of LoginResponseSchema, see LoginPage.tsx)
    # TODO: implement "remember me"
    user = authenticate(username=payload.email, password=payload.password)
    if user is None:
        return LoginResponseSchema(errors=True, message="Invalid username or password", data=None)
    login(request, user)
    return LoginResponseSchema(errors=False, message="Login successful", data={"user": user})


@userflows_api.post("/logout", auth=None, response=LogoutResponseSchema)
def _logout(request) -> LogoutResponseSchema:
    logout(request)
    return LogoutResponseSchema(success=True, message="Logout successful")


@userflows_api.get("/user", response=UserSchema)
def _user(request):
    if request.user.is_authenticated:
        return UserSchema.from_orm(request.user)
    return None


@userflows_api.get("/profile", response=None)  # ProfileSchema)
def _user_profile(request):
    print("HI")
    return request.user.profile
