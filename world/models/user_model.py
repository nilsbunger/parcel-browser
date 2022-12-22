from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# This was originally a copy of AbstractUser in Django source code (django/contrib/auth/base_user.py),
# to allow us to transition to a custom user model,
# following the recipe in comment 18 of https://code.djangoproject.com/ticket/25313#comment:18
# Note that we copied AbstractBaseUser, since we need to change the primary-key username field
class User(AbstractBaseUser, PermissionsMixin):
    class Meta:
        swappable = "AUTH_USER_MODEL"
        # Use the default table name for the user model during migration to a custom user model
        db_table = "auth_user"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        abstract = False

    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


#
# # Read-only shadow of what we get from Auth0
# class Auth0User(models.Model):
#     created = models.DateTimeField(auto_now_add=True)
#     sub = models.OneToOneField('world.User', to_field="sub", unique=True, related_name="auth0_user",
#                                on_delete=models.CASCADE)
#     details = models.JSONField(blank=True, null=True)
#
#     def __str__(self):
#         return "Auth0 sub '{}' is user '{}'".format(self.sub, self.user)
