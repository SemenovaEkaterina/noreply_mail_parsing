import imaplib
import email
import re
import os
import sys
from .connection import make_message_list
from .header_parser import header_parse
from django.core.management.base import BaseCommand
from mail_parsing.models import EmailAddress

#imaplib._MAXLINE = 2000000
SEARCH_FOLDER = 'Trash'

UNDELIVERED_STATUS = [
    '5.0.0',
    '4.4.1', # connection timed out
    '5.4.4',
    '5.7.1',
    '4.4.3',
    '5.4.6', # mail loops back to myself
    '5.2.1',
    '4.0.0', # mail receiving disabled
    '4.1.1', # address rejected: unverified address
    '4.7.1', # You are not allowed to connect
    '4.4.2', # lost connection
    '5.7.606', # Access denied, banned sending IP
    '5.5.0', # user not found
    '4.4.7', # No recipients
    '5.1.2', # recipient address is not a valid
    '5.4.1', # Recipient address rejected: Access denied
    '5.5.4',  # Error: send AUTH command first
]

OVER_QUOTA_STATUS = [
    '4.2.2',
    '5.2.2',
    '5.1.1', # account is full
    '5.7.0', # maildir over quota
]

ADDRESS_FAILED_TEXT = [
    'Unrouteable address',
    '550 Addresses failed:',
    'Mailbox disabled for this recipient',
    'invalid mailbox',
    'does not exist',
]

class Command(BaseCommand):
    def handle(self, *args, **options):

        # message_ids, mail = make_message_list('FROM "MAILER-DAEMON" UNSEEN')
        message_ids, mail = make_message_list('FROM "MAILER-DAEMON"')

        min_id = os.environ.get('MIN_ID', 120000)
        max_id = os.environ.get('MAX_ID', 121000)

        # print("START")
        for i in message_ids:

            msg_num = i.decode()

            if int(msg_num) <= int(min_id) or int(msg_num) > int(max_id):
                continue

            # print()
            # print(i)

            try:
                res, encoded_message = mail.fetch(i, '(RFC822)')
            except imaplib.IMAP4.error:
                continue

            try:
                message = email.message_from_bytes(encoded_message[0][1])
            except email.errors.MessageParseError:
                mail.store(i, '+FLAGS', '\\UNSEEN')
                continue


            invalid_address = None
            no_such_user = False
            limit_exceed = False

            for part in message.walk():
                header_content_type = part.get_content_type()
                if header_content_type is not None:
                    if 'message/delivery-status' == header_content_type.lower():
                        payload = part.get_payload(1)

                        invalid_address = header_parse(payload, 'Original-Recipient')
                        if invalid_address is not None:
                            invalid_address = re.sub(r'rfc822; ?', '', invalid_address)
                        else:
                            invalid_address = header_parse(payload, 'Final-Recipient')
                            if invalid_address is not None:
                                invalid_address = re.sub(r'rfc822; ?', '', invalid_address)

                        if invalid_address is not None:
                            header_status = header_parse(payload, 'Status')
                            if header_status in UNDELIVERED_STATUS:
                                no_such_user = True
                                break
                            if header_status in OVER_QUOTA_STATUS:
                                limit_exceed = True
                                break



                payload = part.get_payload(decode=True)
                if payload is not None:
                    if part.get_content_type() == 'text/plain':
                        charset = part.get_content_charset(failobj=None)
                        if charset is not None:
                            try:
                                decoded_part = payload.decode(str(charset), "ignore")
                            except LookupError:
                                decoded_part = payload.decode()
                        else:
                            decoded_part = str(payload)

                        if decoded_part is not None:
                            header_failed_address = header_parse(message, 'X-Failed-Recipients')
                            if header_failed_address is not None:
                                invalid_address = header_failed_address
                            else:
                                continue

                            if 'messages count limit' in decoded_part:
                                limit_exceed = True
                            for text in ADDRESS_FAILED_TEXT:
                                if text not in decoded_part:
                                    no_such_user = True
                            if 'SMTP error from remote mail server' in decoded_part and 'limit' not in decoded_part:
                                no_such_user = True




            if header_parse(message, 'X-Mailer-Daemon-Error') == 'user_not_found':
                header_failed_address = header_parse(message, 'X-Failed-Recipients')
                if header_failed_address is not None:
                    no_such_user = True
                    invalid_address = header_failed_address
                else:
                    header_failed_address = header_parse(message, 'X-Mailer-Daemon-Recipients')
                    if header_failed_address is not None:
                        no_such_user = True
                        invalid_address = header_failed_address

            if limit_exceed == True:
                limit_exceed_chance = 1
            else:
                limit_exceed_chance = 0
            if ( no_such_user or limit_exceed ) and invalid_address is not None:
                EmailAddress.objects.create(address=invalid_address, limit_exceed_chance=limit_exceed_chance, detected_spam_chance=0)

            '''
            if invalid_address is None and limit_exceed == False and no_such_user:
                mail.store(i, '-FLAGS', '\\SEEN')
                print("UNDEFINED "+str(msg_num))
                r = open('res/full_messages/' + str(msg_num) + '.txt', 'w+')
                try:
                    r.write(message.as_bytes().decode(encoding='UTF-8'))
                except:
                    r.write('error')
            '''

        mail.close()
        mail.logout()
