# Generated by Django 5.0.1 on 2024-09-17 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='IS_ATHLETE',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='IS_COACH',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='IS_EVENT_ORG',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='IS_SCOUT',
        ),
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(blank=True, choices=[('Player', 'Player'), ('Coach', 'Coach'), ('Scout', 'Scout'), ('Event Organizer', 'Event Organizer')], max_length=50, null=True),
        ),
    ]