# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_parsing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='./attachments')),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='quote',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='emailaddress',
            name='detected_spam_chance',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='emailaddress',
            name='limit_exceed_chance',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='message',
            name='in_reply_to_header',
            field=models.CharField(default='', max_length=150),
        ),
        migrations.AlterField(
            model_name='message',
            name='subject',
            field=models.CharField(default='', max_length=150),
        ),
        migrations.AlterField(
            model_name='message',
            name='text',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='attachment',
            name='message',
            field=models.ForeignKey(to='mail_parsing.Message'),
        ),
    ]
