from django.db.models.signals import post_save
from django.dispatch import receiver

from userflows.models import User


# Automatically create a Profile object when a User is created
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    try:
        if created:
            pass
            # Profile.objects.create(user=instance).save()
    except Exception as err:
        print(f"Error creating user profile!\n{err}")
