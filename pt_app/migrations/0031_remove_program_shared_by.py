# Generated by Django 4.2.7 on 2024-05-14 16:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pt_app', '0030_program_shared_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='program',
            name='shared_by',
        ),
    ]
