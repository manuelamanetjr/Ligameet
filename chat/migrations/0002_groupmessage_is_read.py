# Generated by Django 5.1.2 on 2024-11-11 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmessage',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
