# Generated by Django 5.1.1 on 2024-10-18 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainBot', '0005_channel_folowers_alter_channel_external_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='ban_time',
        ),
        migrations.RemoveField(
            model_name='user',
            name='messages_per_second',
        ),
    ]
