# Generated by Django 5.1.1 on 2025-03-04 13:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainBot', '0019_alter_channel_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='channel',
            old_name='name',
            new_name='title',
        ),
    ]
