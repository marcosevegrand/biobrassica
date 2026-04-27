from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.accounts.models import User


class CreateInitialAdminCommandTests(TestCase):
    def test_create_initial_admin_creates_superuser_from_env(self):
        stdout = StringIO()

        with patch.dict(
            'os.environ',
            {
                'INITIAL_ADMIN_EMAIL': 'bootstrap@example.com',
                'INITIAL_ADMIN_USERNAME': 'bootstrap-admin',
                'INITIAL_ADMIN_PASSWORD': 'S3guraPass123!',
            },
            clear=False,
        ):
            call_command('create_initial_admin', stdout=stdout)

        user = User.objects.get(email='bootstrap@example.com')

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('S3guraPass123!'))
        self.assertIn('Initial admin created for bootstrap@example.com.', stdout.getvalue())

    def test_create_initial_admin_is_idempotent_when_user_exists(self):
        existing_user = User.objects.create_superuser(
            email='bootstrap-existing@example.com',
            username='bootstrap-existing',
            password='ExistingPass123!',
        )
        stdout = StringIO()

        with patch.dict(
            'os.environ',
            {
                'INITIAL_ADMIN_EMAIL': 'bootstrap-existing@example.com',
                'INITIAL_ADMIN_USERNAME': 'bootstrap-existing',
                'INITIAL_ADMIN_PASSWORD': 'ChangedPass123!',
            },
            clear=False,
        ):
            call_command('create_initial_admin', stdout=stdout)

        existing_user.refresh_from_db()

        self.assertEqual(User.objects.filter(email='bootstrap-existing@example.com').count(), 1)
        self.assertTrue(existing_user.check_password('ExistingPass123!'))
        self.assertIn('Initial admin already exists for bootstrap-existing@example.com', stdout.getvalue())

    def test_create_initial_admin_rejects_partial_env_configuration(self):
        with patch.dict(
            'os.environ',
            {
                'INITIAL_ADMIN_EMAIL': 'bootstrap-partial@example.com',
                'INITIAL_ADMIN_USERNAME': 'bootstrap-partial',
                'INITIAL_ADMIN_PASSWORD': '',
            },
            clear=False,
        ):
            with self.assertRaises(CommandError):
                call_command('create_initial_admin')