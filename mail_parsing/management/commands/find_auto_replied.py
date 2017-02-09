import email
import imaplib
import os
import re

from django.core.management.base import BaseCommand

from mail_parsing.management.commands.scripts.connection import make_message_list
from mail_parsing.management.commands.scripts.header_parser import header_parse
from mail_parsing.models import EmailAddress
from .parse_mail import UNDELIVERED_STATUS, OVER_QUOTA_STATUS

ADDRESS_FAILED_TEXT = [
    'Unrouteable address',
    '550 Addresses failed:',
    'Mailbox disabled for this recipient',
    'invalid mailbox',
    'does not exist',
]

class Command(BaseCommand):
    def handle(self, *args, **options):

        message_ids, mail = make_message_list('FROM "MAILER-DAEMON" UNSEEN')

        min_id = os.environ.get('MIN_ID', 0)
        max_id = os.environ.get('MAX_ID', 1000000)

        max_count = os.environ.get('MAX_COUNT', 1000)
        count = 0

        for i in message_ids:

            msg_num = i.decode()

            if int(msg_num) <= int(min_id) or int(msg_num) > int(max_id):
                continue

            if count > max_count:
                break

            count += 1

            # print()
            # print(i)

            try:
                res, encoded_message = mail.fetch(i, '(RFC822)')
            except imaplib.IMAP4.error:
                mail.store(i, '-FLAGS', '\\SEEN')
                continue

            try:
                message = email.message_from_bytes(encoded_message[0][1])
            except email.errors.MessageParseError:
                mail.store(i, '-FLAGS', '\\SEEN')
                continue

            invalid_address = None
            no_such_user = False
            limit_exceed = False

            for part in message.walk():

                # Поиск по заголовкам message/delivery-status на предмет кодов ошибок
                # (UNDELIVERED_STATUS, OVER_QUOTA_STATUS)
                if part.get_content_type() == 'message/delivery-status':
                    try:
                        payload = part.get_payload(1)
                    except:
                        continue

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

                # Поиск по тексту письма на пердмет шаблонных выражений (ADDRESS_FAILED_TEXT)
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

            # Специальный заголовок X-Mailer-Daemon-Error: user_not_found
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

            if limit_exceed:
                limit_exceed_chance = 1
            else:
                limit_exceed_chance = 0
            if (no_such_user or limit_exceed) and invalid_address is not None:
                try:
                    EmailAddress.objects.create(address=invalid_address,
                                                limit_exceed_chance=limit_exceed_chance,
                                                detected_spam_chance=0)
                except:
                    print("CANT SAVE " + msg_num)
                    mail.store(i, '-FLAGS', '\\SEEN')
                    try:
                        r = open('res/full_messages/' + str(msg_num) + '.txt', 'w+')
                        r.write(message.as_bytes().decode(encoding='UTF-8'))
                        r.close()
                    except:
                        pass

            if invalid_address is None and limit_exceed is False and no_such_user is False:
                mail.store(i, '-FLAGS', '\\SEEN')
                print("UNDEFINED "+str(msg_num))
                with open('res/full_messages/' + str(msg_num) + '.txt', 'w+') as f:
                    try:
                        f.write(message.__str__())
                    except:
                        try:
                            f.write(message.as_bytes().decode(encoding='UTF-8'))
                        except:
                            f.write('ERROR')

        mail.close()
        mail.logout()
