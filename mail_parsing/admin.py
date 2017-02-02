from django.contrib import admin
from mail_parsing.models import EmailAddress, Attachment, Message

# Register your models here.
admin.site.register(EmailAddress)
admin.site.register(Message)
admin.site.register(Attachment)