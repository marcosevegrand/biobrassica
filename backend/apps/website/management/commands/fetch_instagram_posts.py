import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.website.models import InstagramPost
from apps.website.services import fetch_instagram_posts

logger = logging.getLogger(__name__)

POSTS_TO_KEEP = 5


class Command(BaseCommand):
    help = 'Fetch the latest Instagram posts from the public @biobrassica profile.'

    def handle(self, *args, **options):
        posts_data = fetch_instagram_posts(count=POSTS_TO_KEEP)

        if not posts_data:
            self.stderr.write(self.style.WARNING('No Instagram posts fetched.'))
            return

        saved = 0
        for data in posts_data:
            post, created = InstagramPost.objects.update_or_create(
                instagram_id=data['instagram_id'],
                defaults={
                    'image_url': data['image_url'],
                    'caption': data['caption'],
                    'permalink': data['permalink'],
                    'posted_at': data['posted_at'],
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
        kept = active_posts.order_by('-posted_at', '-pk')[:POSTS_TO_KEEP]
        kept_ids = set(kept.values_list('pk', flat=True))

        deactivated = (
            active_posts.exclude(pk__in=kept_ids)
            .update(is_active=False)
        )
        if deactivated:
            self.stdout.write(f'Deactivated {deactivated} older post(s).')

        self.stdout.write(
            self.style.SUCCESS(f'Done. {saved} new, {len(posts_data)} total, {deactivated} deactivated.')
        )
