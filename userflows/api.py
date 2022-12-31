from ninja import NinjaAPI
from ninja.security import django_auth

from .api_schema import ProfileSchema

userflows_api = NinjaAPI(auth=django_auth, csrf=True, urls_namespace="userflows")


################################################################################################
## User info API
################################################################################################
@userflows_api.get("/profile", response=ProfileSchema)
def user_profile(request):
    print("HI")
    return request.user.profile
