import logging
import re


EMAIL_RE = re.compile(r'([A-Z0-9._%+-]{2})[A-Z0-9._%+-]*@([A-Z0-9.-]+\.[A-Z]{2,})', re.IGNORECASE)
PHONE_RE = re.compile(r'(?<!\d)(\+?\d[\d\s-]{6,}\d)(?!\d)')


def _mask_phone(match):
    phone = match.group(1)
    if len(phone) <= 5:
        return '*' * len(phone)
    return f'{phone[:3]}***{phone[-2:]}'


class RedactingFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        message = EMAIL_RE.sub(lambda match: f'{match.group(1)}***@{match.group(2)}', message)
        message = PHONE_RE.sub(_mask_phone, message)

        record.msg = message
        record.args = ()
        return True