# Generated by Django 5.0.7 on 2024-10-14 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ligameet', '0004_event_event_image_alter_event_event_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='EVENT_IMAGE',
            field=models.ImageField(blank=True, default='event_default.png', upload_to='event_images/'),
        ),
    ]
