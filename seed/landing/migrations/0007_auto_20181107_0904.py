# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-07 17:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0006_auto_20170602_1648'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seeduser',
            name='api_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=128, verbose_name='api key'),
        ),
    ]
