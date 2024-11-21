# Generated by Django 5.0.1 on 2024-11-21 07:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ligameet', '0026_match_event'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='match',
            name='TEAM1_ID',
        ),
        migrations.RemoveField(
            model_name='match',
            name='TEAM2_ID',
        ),
        migrations.RemoveField(
            model_name='match',
            name='event',
        ),
        migrations.AddField(
            model_name='match',
            name='TEAM_ID',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ligameet.team'),
        ),
        migrations.CreateModel(
            name='MatchDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_date', models.DateTimeField(blank=True, null=True)),
                ('match_type', models.CharField(blank=True, max_length=50, null=True)),
                ('match_category', models.CharField(blank=True, max_length=50, null=True)),
                ('match_status', models.CharField(blank=True, max_length=50, null=True)),
                ('match', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='ligameet.match')),
                ('sport', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ligameet.sportdetails')),
                ('team1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_team', to='ligameet.team')),
                ('team2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='away_team', to='ligameet.team')),
            ],
        ),
    ]