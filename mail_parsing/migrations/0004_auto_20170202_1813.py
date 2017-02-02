# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_parsing', '0003_auto_20170202_1812'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='original',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='message',
            name='status',
            field=models.IntegerField(default=2),
        ),
    ]
