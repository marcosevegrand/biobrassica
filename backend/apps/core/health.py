from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """Simple health check endpoint for Docker and monitoring."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)
