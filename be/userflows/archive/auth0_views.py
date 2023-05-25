import json
from urllib.parse import quote_plus, urlencode

from authlib.integrations.base_client import OAuthError
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout

from userflows.models import User

# Based on https://auth0.com/docs/quickstart/webapp/django/01-login#configure-auth0

### AUTH0 view file
oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)


def login(request):
    return oauth.auth0.authorize_redirect(request, request.build_absolute_uri(reverse("auth0_callback")))


# The callback route is responsible for actually saving the session for the user and logging them in.
def callback(request):
    try:
        token = oauth.auth0.authorize_access_token(request)
    except OAuthError as e:
        if e.error == "unauthorized":
            # if user is blocked this will happen.
            print(f"User is unauthorized: {e.description}")
        else:
            print("Unknown Oauth Error: ", e)
        return redirect(request.build_absolute_uri(reverse("auth0_index")))

    request.session["user"] = token
    user, user_created = User.objects.get_or_create(
        sub=token["userinfo"]["sub"], defaults={"email": token["userinfo"]["email"]}
    )
    # auth0_user, auth0_user_created = Auth0User.objects.get_or_create(
    #     sub=user, defaults={"details": token["userinfo"]}
    # )
    # active=False
    # if active:
    #     django_login(request, auth0_user.user)
    # else:
    #     # Add a message here
    #     print ("NOT LOGGED IN")
    #     pass

    return redirect(request.build_absolute_uri(reverse("auth0_index")))


# logout: clear the user's session in your app, redirect to Auth0's logout endpoint
# to ensure their session is completely clear, before they are returned to your home route
def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("auth0_index")),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


# Home - either render an authenticated user's details, or offer to allow visitors to sign in.
def index(request):
    return render(
        request,
        "world/auth_index.html",
        context={
            "session": request.session.get("user"),
            "pretty": json.dumps(request.session.get("user"), indent=4),
        },
    )
