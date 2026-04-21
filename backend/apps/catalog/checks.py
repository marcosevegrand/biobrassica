from django.core.checks import Warning, register
from django.db.utils import OperationalError, ProgrammingError

from apps.catalog.models import Location


@register()
def active_pickup_locations_have_checkout_codes(app_configs, **kwargs):
    try:
        missing_locations = list(
            Location.objects.filter(is_active=True, pickup_location_code='').order_by('name').values_list('name', flat=True)
        )
    except (OperationalError, ProgrammingError):
        return []

    if not missing_locations:
        return []

    sample = ', '.join(missing_locations[:3])
    if len(missing_locations) > 3:
        sample = f'{sample}, ...'

    return [
        Warning(
            'Existem localizações ativas sem pickup_location_code configurado.',
            hint=f'Defina o código de checkout nas localizações ativas: {sample}',
            id='catalog.W001',
        ),
    ]