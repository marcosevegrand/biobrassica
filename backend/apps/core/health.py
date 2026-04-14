import logging

from django.db import connection
from django.http import JsonResponse


logger = logging.getLogger(__name__)


def health_check(request):
    """Simple health check endpoint for Docker and monitoring."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok'})
    except Exception:
        logger.exception('Health check failed')
        return JsonResponse({'status': 'error'}, status=500)
