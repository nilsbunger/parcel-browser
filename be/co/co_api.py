from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI
from ninja.security import django_auth

api = NinjaAPI(auth=django_auth, csrf=True, urls_namespace="co", docs_decorator=staff_member_required)
