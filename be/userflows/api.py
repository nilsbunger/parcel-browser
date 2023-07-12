import sesame
import sesame.utils
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.urls import reverse
from lib.ninja_api import ApiResponseSchema
from ninja import ModelSchema, NinjaAPI, Schema
from ninja.errors import ValidationError
from ninja.security import django_auth
from pydantic import EmailStr, constr

from .lib import send_magic_link_email
from .models import User

# from .api_schema import ProfileSchema

userflows_api = NinjaAPI(
    auth=django_auth, csrf=True, urls_namespace="userflows", docs_decorator=staff_member_required
)


################################################################################################
## User info API
################################################################################################


class LoginSchema(Schema):
    email: EmailStr
    # string constraint - https://docs.pydantic.dev/1.10/usage/types/#arguments-to-constr
    password: constr(min_length=8, max_length=32)
    rememberMe: bool = False  # noqa: n806 - should be lowercase


class MagicLinkLoginSchema(Schema):
    email: EmailStr
    rememberMe: bool = False  # noqa: n806 - should be lowercase


class UserSchema(ModelSchema):
    class Config:
        model = User
        model_fields = ["first_name", "last_name", "email"]


class _LoginResponseDataSchema(Schema):
    user: UserSchema = None


LoginResponseSchema = ApiResponseSchema[_LoginResponseDataSchema]


LogoutResponseSchema = ApiResponseSchema[None]


@userflows_api.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    # flush validation errors to console.
    print(exc.errors)
    return userflows_api.create_response(request, {"detail": exc.errors}, status=422)


# Magic_link_login endpoint: allow unauthenticated access
@userflows_api.post("/login", auth=None, response=LoginResponseSchema)
def _login(request, payload: LoginSchema):
    ...
    # TODO: better validation and rate-limiting here to prevent bad login attempts. See what django-allauth did?
    # TODO: implement "remember me"
    user = authenticate(username=payload.email, password=payload.password)
    if user is None:
        return LoginResponseSchema(errors=True, message="Invalid username or password", data=None)
    login(request, user)
    return LoginResponseSchema(errors=False, message="Login successful", data={"user": user})


@userflows_api.post("/magic_link_login", auth=None, response=LoginResponseSchema)
def _magic_link_login(request, payload: MagicLinkLoginSchema):
    ...
    # TODO: better validation and rate-limiting here to prevent bad login attempts. See what django-allauth did?
    # TODO: implement "remember me"
    User = get_user_model()  # noqa: N806
    user = User.objects.get_or_create(email=payload.email)
    # user = authenticate(username=payload.email, password=payload.password)
    if user is None:
        return LoginResponseSchema(errors=True, message="We can't create an account with that email", data=None)

    # Create a magic link for this user.
    link = reverse("magic_link_auth")
    link = request.build_absolute_uri(link)
    link += sesame.utils.get_query_string(user)
    send_magic_link_email(user, link)
    return LoginResponseSchema(errors=False, message="Email sent", data={"user": None})


@userflows_api.post("/logout", auth=None, response=LogoutResponseSchema)
def _logout(request) -> LogoutResponseSchema:
    logout(request)
    return LogoutResponseSchema(success=True, message="Logout successful")


@userflows_api.get("/user", response=UserSchema)
def _user(request) -> UserSchema | None:
    if request.user.is_authenticated:
        return UserSchema.from_orm(request.user)
    return None


@userflows_api.get("/profile", response=None)  # ProfileSchema)
def _user_profile(request):
    return request.user.profile
