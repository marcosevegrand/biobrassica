import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Reset the password of a staff/admin account identified by email.'

    def add_arguments(self, parser):
        parser.add_argument('email', help='Email address of the admin/staff account to reset.')
        parser.add_argument(
            '--allow-non-staff',
            action='store_true',
            help='Allow resetting a non-staff account as well.',
        )

    def handle(self, *args, **options):
        email = (options['email'] or '').strip().lower()
        allow_non_staff = bool(options['allow_non_staff'])
        user_model = get_user_model()

        try:
            user = user_model._default_manager.get(email=email)
        except user_model.DoesNotExist as error:
            raise CommandError(f'No user found with email {email}.') from error

        if not allow_non_staff and not user.is_staff:
            raise CommandError('Refusing to reset a non-staff account. Use --allow-non-staff to override.')

        password = getpass.getpass('New password: ')
        password_confirmation = getpass.getpass('Confirm new password: ')

        if password != password_confirmation:
            raise CommandError('Passwords do not match.')

        validate_password(password, user=user)
        user.set_password(password)
        user.save(update_fields=['password'])

        self.stdout.write(self.style.SUCCESS(f'Password updated for {user.email}.'))