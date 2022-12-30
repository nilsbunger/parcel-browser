from ninja import NinjaAPI
from ninja.security import django_auth

# Django-ninja authentication guide: https://django-ninja.rest-framework.com/guides/authentication/

# Require auth on all API routes (can be overriden if needed)
ninja_api = NinjaAPI(auth=django_auth, csrf=True)
