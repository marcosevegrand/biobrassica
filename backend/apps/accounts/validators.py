from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def normalize_portuguese_nif(value):
    if value in (None, ''):
        return ''

    return ''.join(character for character in str(value) if character.isdigit())


def validate_portuguese_nif(value):
    normalized_value = normalize_portuguese_nif(value)
    if normalized_value == '':
        return

    if len(normalized_value) != 9:
        raise ValidationError(_('Indique um NIF português válido.'))

    check_digit_total = sum(int(digit) * weight for digit, weight in zip(normalized_value[:8], range(9, 1, -1), strict=False))
    expected_check_digit = 11 - (check_digit_total % 11)
    if expected_check_digit >= 10:
        expected_check_digit = 0

    if int(normalized_value[-1]) != expected_check_digit:
        raise ValidationError(_('Indique um NIF português válido.'))