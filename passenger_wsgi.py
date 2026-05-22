import os
import sys

# Add the backend directory to the Python path so Django can be imported.
# This file lives in the application root (e.g. /home/user/biobrassica/).
# The Django project lives in backend/.
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(APP_ROOT, 'backend')
sys.path.insert(0, BACKEND_DIR)

# cPanel Application Manager already sets environment variables configured
# in the UI.  Fall back to production settings if not set.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
