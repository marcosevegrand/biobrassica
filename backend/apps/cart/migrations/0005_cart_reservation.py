from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0004_cart_login_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='reserved_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='reserved_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
