import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_alter_order_created_at_alter_order_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='access_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]