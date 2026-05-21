import os
import re

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible


ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'tif'}

SUSPICIOUS_EXTENSION_RE = re.compile(r'\.(?:html?|xhtml|xml|svg|js|mjs|json|css|php|phtml|pl|py|sh|cgi|exe|dll|bat|cmd)$', re.IGNORECASE)


def _normalize_extension(filename):
    return os.path.splitext(filename)[1].lstrip('.').lower()


@deconstructible
class SafeImageExtensionValidator(FileExtensionValidator):
    def __init__(self):
        super().__init__(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)


def validate_no_suspicious_extension(value):
    if SUSPICIOUS_EXTENSION_RE.search(str(value.name)):
        raise ValidationError('O ficheiro tem uma extensão não permitida.')


def validate_image_upload(value):
    ext = _normalize_extension(value.name)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f'A extensão .{ext} não é permitida para imagens. '
            f'Use: {", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))}.'
        )
