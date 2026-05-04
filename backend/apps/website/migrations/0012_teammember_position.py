from django.db import migrations, models


def forwards_team_member_positions(apps, schema_editor):
    TeamMember = apps.get_model('website', 'TeamMember')
    TeamMemberPosition = apps.get_model('website', 'TeamMemberPosition')

    for team_member in TeamMember.objects.order_by('order', 'name', 'pk'):
        TeamMemberPosition.objects.update_or_create(
            team_member=team_member,
            defaults={'position': team_member.order},
        )


def backwards_team_member_positions(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0011_remove_payment_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamMemberPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='posição')),
                ('team_member', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='sort_order', to='website.teammember', verbose_name='membro da equipa')),
            ],
            options={
                'verbose_name': 'ordem de membro da equipa',
                'verbose_name_plural': 'ordens de membros da equipa',
                'ordering': ['position', 'pk'],
            },
        ),
        migrations.RunPython(forwards_team_member_positions, backwards_team_member_positions),
        migrations.RemoveField(
            model_name='teammember',
            name='order',
        ),
    ]
