from django.core.management.base import BaseCommand
from .scripts.connection import make_message_list
import imaplib
import os

class Command(BaseCommand):
    def handle(self, *args, **options):
        message_ids, mail = make_message_list('ALL')

        print(len(message_ids))
        min_id = os.environ.get('MIN_ID', 60000)
        max_id = os.environ.get('MAX_ID', 62000)

        for i in message_ids:


            msg_num = i.decode()


            if int(msg_num) <= int(min_id) or int(msg_num) > int(max_id):
                continue

            print(i)
            mail.store(i, '-FLAGS', '\\SEEN')


        mail.close()
        mail.logout()
