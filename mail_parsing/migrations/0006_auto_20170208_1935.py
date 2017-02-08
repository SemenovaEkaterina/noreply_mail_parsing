# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_parsing', '0005_auto_20170205_2113'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='message',
            index_together=set([('id', 'status', 'type'), ('id', 'status')]),
        ),
    ]
