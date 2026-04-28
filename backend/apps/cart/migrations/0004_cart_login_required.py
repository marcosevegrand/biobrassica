from django.conf import settings
from django.db import migrations, models


def delete_anonymous_carts(apps, schema_editor):
    Cart = apps.get_model('cart', 'Cart')
    Cart.objects.filter(user__isnull=True).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_cartitem_quantity_limits'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(delete_anonymous_carts, noop_reverse),
        migrations.RemoveConstraint(
            model_name='cart',
            name='cart_unique_non_empty_session_key',
        ),
        migrations.RemoveField(
            model_name='cart',
            name='session_key',
        ),
        migrations.AlterField(
            model_name='cart',
            name='user',
            field=models.OneToOneField(
                on_delete=models.deletion.CASCADE,
                related_name='cart',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
