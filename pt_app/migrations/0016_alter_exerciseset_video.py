# Generated by Django 4.2.7 on 2024-04-23 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pt_app', '0015_workoutsession_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exerciseset',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='workout_videos/'),
        ),
    ]
