from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.catalog.models import Location
from apps.core.site_content import clear_contact_locations_cache


@receiver(post_save, sender=Location)
@receiver(post_delete, sender=Location)
def invalidate_contact_locations_cache(**kwargs):
    clear_contact_locations_cache()