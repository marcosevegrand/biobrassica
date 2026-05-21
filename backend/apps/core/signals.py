from django.db.models import FileField
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.catalog.models import Location
from apps.core.site_content import clear_contact_locations_cache
from apps.core.validators import validate_image_upload


@receiver(post_save, sender=Location)
@receiver(post_delete, sender=Location)
def invalidate_contact_locations_cache(**kwargs):
    clear_contact_locations_cache()


@receiver(pre_save)
def validate_file_uploads(sender, instance, **kwargs):
    for field in sender._meta.get_fields():
        if not isinstance(field, FileField):
            continue
        file_obj = getattr(instance, field.attname, None)
        if file_obj and hasattr(file_obj, 'name') and file_obj.name:
            validate_image_upload(file_obj)