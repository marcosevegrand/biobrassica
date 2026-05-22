from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.website.models import InstagramPost
from apps.website.services import fetch_instagram_posts

POSTS_TO_KEEP = 5
INSTAGRAM_BASE_URL = 'https://www.instagram.com'


class Command(BaseCommand):
    help = (
        'Populate Instagram posts from INSTAGRAM_POST_SHORTCODES setting '
        'or from shortcodes passed as arguments.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'shortcodes',
            nargs='*',
            help='Instagram post shortcodes (e.g. DFOdgqNtgvb)',
        )

    def handle(self, *args, **options):
        shortcodes = options.get('shortcodes') or []

        if shortcodes:
            posts_data = [
                {
                    'instagram_id': sc,
                    'permalink': f'{INSTAGRAM_BASE_URL}/p/{sc}/',
                }
                for sc in shortcodes
            ]
        else:
            posts_data = fetch_instagram_posts(count=POSTS_TO_KEEP)

        if not posts_data:
            self.stderr.write(self.style.WARNING(
                'No Instagram posts found. '
                'Pass shortcodes as arguments or set INSTAGRAM_POST_SHORTCODES in settings.'
            ))
            return

        saved = 0
        for i, data in enumerate(posts_data):
            post, created = InstagramPost.objects.update_or_create(
                instagram_id=data['instagram_id'],
                defaults={
                    'permalink': data.get('permalink', ''),
                    'image_url': data.get('image_url', ''),
                    'caption': data.get('caption', ''),
                    'posted_at': data.get('posted_at'),
                    'sort_order': i,
                    'is_active': True,
                },
            )
            if created:
                saved += 1
                self.stdout.write(
                    self.style.SUCCESS(f'New post: {data["instagram_id"]}')
                )
            else:
                self.stdout.write(f'Updated: {data["instagram_id"]}')

        active_posts = InstagramPost.objects.filter(is_active=True)
        kept = active_posts.order_by('sort_order')[:POSTS_TO_KEEP]
        kept_ids = set(kept.values_list('pk', flat=True))

        deactivated = active_posts.exclude(pk__in=kept_ids).update(is_active=False)
        if deactivated:
            self.stdout.write(f'Deactivated {deactivated} older post(s).')

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {saved} new, {len(posts_data)} total, '
                f'{deactivated} deactivated.'
            )
        )
