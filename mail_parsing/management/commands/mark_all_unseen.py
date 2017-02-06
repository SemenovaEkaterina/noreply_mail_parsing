from django.core.management.base import BaseCommand
from .scripts.connection import make_message_list
import imaplib

class Command(BaseCommand):
    def handle(self, *args, **options):

        count = 0
        while True:
            if count > 10:
                break
            message_ids, mail = make_message_list('SEEN')

            print(len(message_ids))
            count += 1
            try:
                mail.store("1:*", '-FLAGS', '\\SEEN')
                #mail.store("12731", '-FLAGS', '\\SEEN')
            except imaplib.IMAP4.abort:
                continue

            mail.close()
            mail.logout()
            break

