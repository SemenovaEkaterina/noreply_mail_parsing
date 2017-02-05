import hashlib
from django.db import models

def upload_to(instance, filename):
    m = hashlib.md5()
    m.update(filename.encode('utf-8'))

    file_path = ''
    for i in m.hexdigest()[:4]:
        file_path += i + '/'

    return file_path+filename


class EmailAddress(models.Model):
    address = models.EmailField(max_length=75, blank=False)
    limit_exceed_chance = models.IntegerField(default=0)
    detected_spam_chance = models.IntegerField(default=0)


class Message(models.Model):
    msg_from = models.EmailField(max_length=75)
    subject = models.CharField(max_length=150, default='')
    in_reply_to_header = models.CharField(max_length=150, default='')
    # 0 - responses, 1 - other
    type = models.IntegerField(default=1)
    # status: 0 - accepted; 1 - unaccepted; 2 - undefined
    status = models.IntegerField(default=2)
    text = models.TextField(default='')
    quote = models.TextField(default='')
    original = models.TextField(default='')


class Attachment(models.Model):
    file = models.FileField(upload_to=upload_to, blank=False)
    message = models.ForeignKey('Message', blank=False)

