# Generated by Django 5.1.2 on 2024-10-19 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ligameet', '0013_invitation_confirmed_at_invitation_sent_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='SPORT_ID',
        ),
        migrations.AddField(
            model_name='event',
            name='CONTACT_PERSON',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='CONTACT_PHONE',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='SPORT',
            field=models.ManyToManyField(related_name='events', to='ligameet.sport'),
        ),
        migrations.AddField(
            model_name='sport',
            name='SPORT_CATEGORY',
            field=models.CharField(choices=[('5v5', '5v5 Full-Court Basketball'), ('3v3', '3v3 Half-Court Basketball'), ('1v1', '1v1 Streetball')], default='5v5', max_length=20),
        ),
        migrations.AddField(
            model_name='team',
            name='TEAM_LOGO',
            field=models.ImageField(blank=True, null=True, upload_to='team_logo_images/'),
        ),
        migrations.AlterField(
            model_name='event',
            name='EVENT_STATUS',
            field=models.CharField(choices=[('upcoming', 'Upcoming'), ('ongoing', 'Ongoing'), ('finished', 'Finished'), ('cancelled', 'Cancelled')], default='upcoming', max_length=10),
        ),
    ]