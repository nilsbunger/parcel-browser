from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema
from ninja.security import django_auth

# from .api_schema import ProfileSchema

userflows_api = NinjaAPI(
    auth=django_auth, csrf=True, urls_namespace="userflows", docs_decorator=staff_member_required
)


################################################################################################
## User info API
################################################################################################


class LoginSchema(Schema):
    email: str
    password: str
    rememberMe: bool = False


class LoginResponseSchema(Schema):
    success: bool
    message: str
    user: dict = None


@userflows_api.post("/login", response=LoginResponseSchema)
def login(request, payload: LoginSchema):
    ...
    # TODO: better validation and rate-limiting here to prevent bad login attempts. See what django-allauth did?
    # TODO: implement "remember me"
    user = authenticate(username=payload.email, password=payload.password)
    if user is None:
        return LoginResponseSchema(success=False, message="Invalid username or password")
    login(request, user)
    return LoginResponseSchema(success=True, message="Login successful", user=user)


@userflows_api.get("/profile", response=None)  # ProfileSchema)
def user_profile(request):
    print("HI")
    return request.user.profile
