import os
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create the initial superuser from INITIAL_ADMIN_* environment variables if it does not exist yet.'

    def handle(self, *args, **options):
        del args, options

        email = str(os.environ.get('INITIAL_ADMIN_EMAIL', '') or '').strip().lower()
        username = str(os.environ.get('INITIAL_ADMIN_USERNAME', '') or '').strip()
        password = str(os.environ.get('INITIAL_ADMIN_PASSWORD', '') or '')

        if not any((email, username, password)):
            self.stdout.write('Skipping initial admin bootstrap: INITIAL_ADMIN_* env vars are not set.')
            return

        missing = []
        if not email:
            missing.append('INITIAL_ADMIN_EMAIL')
        if not username:
            missing.append('INITIAL_ADMIN_USERNAME')
        if not password:
            missing.append('INITIAL_ADMIN_PASSWORD')
        if missing:
            raise CommandError(
                'Missing required environment variables for initial admin bootstrap: ' + ', '.join(missing)
            )

        user_model = get_user_model()
        manager = cast(Any, user_model._default_manager)

        existing_user = manager.filter(email=email).first()
        if existing_user is not None:
            self.stdout.write(self.style.SUCCESS(f'Initial admin already exists for {email}; leaving it unchanged.'))
            return

        if manager.filter(username=username).exists():
            raise CommandError(f'Cannot create initial admin because username {username} is already in use.')

        validate_password(password)
        manager.create_superuser(email=email, username=username, password=password)
        self.stdout.write(self.style.SUCCESS(f'Initial admin created for {email}.'))