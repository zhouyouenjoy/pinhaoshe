
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Photo


@receiver(post_save, sender=Photo)
def photo_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Photo post_save
    """
    if created:
        # Handle newly created photo
        pass


@receiver(post_delete, sender=Photo)
def photo_post_delete(sender, instance, **kwargs):
    """
    Signal handler for Photo post_delete
    """
    # Handle photo deletion
    pass
    