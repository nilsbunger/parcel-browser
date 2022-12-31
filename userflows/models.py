from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    # This was originally a copy of AbstractUser in Django source code (django/contrib/auth/base_user.py),
    # to allow us to transition to a custom user model,
    # following the recipe in comment 18 of https://code.djangoproject.com/ticket/25313#comment:18
    # Note that we copied AbstractBaseUser, since we need to change the primary-key username field
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
    email_verified_ts = models.DateTimeField(_("email verified date"), default=None, null=True)

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

    _token_generator = PasswordResetTokenGenerator()

    # Token for email verification
    def get_verif_token(self):
        return self._token_generator.make_token(self)

    def verify_token(self, token):
        if self._token_generator.check_token(self, token):
            self.is_active = True
            self.email_verified_ts = timezone.now()
            self.save()
            return True
        return False


# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     phone = models.CharField(max_length=20, blank=True)
#     address = models.CharField(max_length=100, blank=True)
#     city = models.CharField(max_length=100, blank=True)
#     state = models.CharField(max_length=2, blank=True)
#     zip = models.CharField(max_length=10, blank=True)
#
#     def __str__(self):
#         return self.user.email
