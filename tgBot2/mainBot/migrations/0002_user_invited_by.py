# Generated by Django 5.1.1 on 2024-10-11 16:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainBot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='invited_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Пригласил', to='mainBot.user'),
        ),
    ]
