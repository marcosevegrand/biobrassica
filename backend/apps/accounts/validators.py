from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def _normalize_digits(value):
    digits = ''.join(character for character in str(value or '') if character.isdigit())
    if digits.startswith('00'):
        return digits[2:]
    return digits


def _extract_portuguese_number(value, *, allowed_prefixes):
    digits = _normalize_digits(value)
    if digits == '':
        return ''

    if len(digits) == 9 and digits[0] in allowed_prefixes:
        return digits

    if len(digits) == 12 and digits.startswith('351') and digits[3] in allowed_prefixes:
        return digits[3:]

    return None


def _format_portuguese_number(national_number):
    return f'{national_number[:3]} {national_number[3:6]} {national_number[6:]}'


def normalize_portuguese_phone(value):
    national_number = _extract_portuguese_number(value, allowed_prefixes={'2', '9'})
    if national_number == '':
        return ''
    if national_number is None:
        raise ValidationError(_('Indique um número de telefone português válido.'))
    return _format_portuguese_number(national_number)


def validate_portuguese_phone(value):
    normalize_portuguese_phone(value)


def normalize_portuguese_mobile_phone(value):
    national_number = _extract_portuguese_number(value, allowed_prefixes={'9'})
    if national_number == '':
        return ''
    if national_number is None:
        raise ValidationError(_('Indique um telemóvel português válido.'))
    return _format_portuguese_number(national_number)


def validate_portuguese_mobile_phone(value):
    normalize_portuguese_mobile_phone(value)


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