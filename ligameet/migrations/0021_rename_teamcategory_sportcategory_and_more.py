# Generated by Django 5.1.2 on 2024-11-19 13:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ligameet', '0020_event_registration_deadline'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TeamCategory',
            new_name='SportCategory',
        ),
        migrations.RenameField(
            model_name='sportdetails',
            old_name='team_category',
            new_name='sport_category',
        ),
    ]
