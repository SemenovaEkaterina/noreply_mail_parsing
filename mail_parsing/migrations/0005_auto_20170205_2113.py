# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mail_parsing.models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_parsing', '0004_auto_20170202_1813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(upload_to=mail_parsing.models.upload_to),
        ),
        migrations.AlterField(
            model_name='emailaddress',
            name='detected_spam_chance',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='emailaddress',
            name='limit_exceed_chance',
            field=models.IntegerField(default=0),
        ),
    ]
