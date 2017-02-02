import imaplib
import mail_parsing.management.commands.parser as parser
import email
import os
import sys
import re
import hashlib
import mail_parsing.management.commands.header_parser as header_parser
import signal
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from django.core.files import File
from mail_parsing.models import EmailAddress, Message, Attachment
from noreply_mail_parsing.settings import STATIC_ROOT

imaplib._MAXLINE = 2000000
SEARCH_FOLDER = 'Trash'

WRONG_HEADERS_VALS = [
    ('Auto-Submitted', 'auto-replied'),
    ('auto-submitted', 'auto-generated'),
    ('Precedence', 'bulk'),
    #('X-Autoreply', 'yes'),
    #('X-Autoreply', 'Yes'),
    ('X-Autoreply', ''),
    ('X-Autogenerated', 'Reply'),
    ('X-Failed-Recipients', ''),
    ('X-Mailer-Daemon-Recipients', ''),
    ('X-MS-Exchange-Message-Is-Ndr', ''),
    ('x-ms-exchange-generated-message-source', 'Mailbox Rules Agent'),
    ('X-MS-Exchange-Inbox-Rules-Loop', ''), #                      ?
    ('X-Auto-Response-Suppress', 'All'), # не факт
]


# также есть X-Auto-Response-Suppress: All
# он используется MS Exchange, чтобы два сервера не обменивались бесконечно автоответами
# можно тоже использовать как критерий автоответа, но с осторожностью

# Отсутствует: в начале темы тоже м.б.
WRONG_SUBJECTS_CONTAINS = [
    'Mail failure.',
    'Undelivered Mail Returned to Sender',
    'Undeliverable mail: ',
    'failure notice',
    'Не удается доставить: ',
    'Delivery Status Notification (Failure)',
    'Undeliverable: ',
    'Delivery Notification: Delivery has failed',
    'Automatic reply: ',
    'Delivery failure',
    'Карантин (Quarantine)',
    '- User unknown!',
    'Автоматический ответ: ',
    'Доставка отложена:',
    'Auto reply: ',
    'Undeliverable mail:',
    'Returned mail: see transcript for details',
    'Mail Delivery Failure',
    'Mail delivery failed: returning message to sender',
    'Unzustellbar:',
    'perm error',
    'Delivery status notification',
    'Warning: message ',
]


WRONG_FROM_CONTAINS = [
    'mailer-daemon',
    'postmaster',
    'spamfilter.admin',
    'mdaemon at ',
    'mail-daemon',
]


# Mailbox size limit exceed
LIMIT_EXCEED_HEADERS_VALS = [
    ('X-Mailer-Daemon-Error', 'full_mailbox'),
]

LIMIT_EXCEED_TEXT = [
    'maximum mailbox size',
    'Mailbox size limit exceeded',
    'mailbox is full',
    # 'temporary',
    'Recipient address rejected: Recipient undeliverable (not exists, blocked, over qouta, etc)',
    'messages count limit',
    'email account that you tried to reach is over quota',
    '552-5.2.2', # mailbox quota exceeded for this recipient
    '552 5.2.2',
    '552-5.2.3', # Message exceeds local size limit
    '552 5.2.3',
    '554-5.7.1', # Access denied            ?
    '554 5.7.1',
]

# Invalid address:
# 'invalid mailbox'
# 'user not found'
# 'No Such User Here'
# 'User unknown'
# 'email account that you tried to reach does not exist'
# 'Unrouteable address'
# '550-5.1.1' # addr not found
# '550 5.1.1'
# '550-5.2.1'
# '550 5.2.1'
# 'No such user!'
# '550-5.7.1' # No such user
# '550 5.7.1'
# 'account is disabled' #                 ?

# SPAM


def parse_timeout_signal_handler(signum, frame):
    raise Exception("Time Out")


class Command(BaseCommand):
    def handle(self, *args, **options):

        mail = imaplib.IMAP4_SSL('imap.gmail.com')

        try:
            mail.login(os.environ.get('EMAIL'), os.environ.get('PASSWORD'))
        except imaplib.IMAP4.error:
            sys.exit(1)

        try:
            res, folders = mail.list()
        except imaplib.IMAP4.error:
            sys.exit(1)
        print('OK: received folders')

        found_folder = False
        for folder in folders:
            if SEARCH_FOLDER in str(folder):
                found_folder = folder

        if found_folder is not None:
            print('OK: found folder')
        else:
            print('ERROR: failed to find a folder')
            sys.exit(1)

        folder_name = [x for x in str(found_folder).split('"') if 'Gmail' in x].pop()

        # "INBOX"
        # folder_name = [x for x in str(found_folder).split('"')][-2]

        try:
            res, sel_data = mail.select(folder_name)
        except imaplib.IMAP4.error:
            print('ERROR: failed to select a folder')
            sys.exit(1)

        print('OK: selected folder, message counter:', int(sel_data.pop()))

        try:
            res, data = mail.search(None, 'ALL')
        except imaplib.IMAP4.error:
            sys.exit(1)

        print('OK: received a list of messages')

        if len(data) > 0:
            message_ids = data.pop().split()
        else:
            message_ids = []

        min_id = os.environ.get('MIN_ID', 174097)
        max_id = os.environ.get('MAX_ID', 174098)

        for i in message_ids:

            msg_num = i.decode()

            if int(msg_num) <= int(min_id) or int(msg_num) > int(max_id):
                continue

            print()
            print(i)

            try:
                res, encoded_message = mail.fetch(i, '(RFC822)')
            except imaplib.IMAP4.error:
                sys.exit(1)

            try:
                message = email.message_from_bytes(encoded_message[0][1])
            except email.errors.MessageParseError:
                pass

            '''
            r = open('res/full_messages/' + str(msg_num) + '.txt', 'w+')
            r.write(message.as_bytes().decode(encoding='UTF-8'))
            '''

            go_next = False

            invalid_address = 0
            autoreply = 0

            # Autoreply
            # Ex:
            # Reply-To: 123.autoreply@gmail.com
            # Return-Path: 123.autoreply@gmail.com or MAILER-DAEMON@corp.mail.ru
            # Errors-To: 123.autoreply@gmail.com

            if header_parser.header_parse(message, 'Reply-To') is not None:
                if 'autoreply' in header_parser.header_parse(message, 'Reply-To').lower():
                    autoreply += 0.2

            if header_parser.header_parse(message, 'Return-Path') is not None:
                for wrong_from in WRONG_FROM_CONTAINS:
                    if wrong_from in header_parser.header_parse(message, 'Return-Path').lower():
                        autoreply += 0.2
                if 'autoreply' in header_parser.header_parse(message, 'Return-Path').lower():
                    autoreply += 0.2

            if header_parser.header_parse(message, 'Errors-To') is not None:
                if 'autoreply' in header_parser.header_parse(message, 'Errors-To'):
                    autoreply += 0.2

            # error -> text/plain
            if message.get_content_type() == 'multipart/report':
                invalid_address += 0.2
                for param in message.get_params(failobj=[]):
                    if param[0] == 'report-type' and param[1] == 'delivery-status':
                        # print('FILTERED T')
                        invalid_address += 0.2

            # message.__getitem__(): er -> None
            # Если автоответ, то со оригинального адреса
            wrong_from_in = False
            if message['From'] is not None:
                message_from = header_parser.header_parse(message, 'From')
                if message_from is not None:
                    for wrong_from in WRONG_FROM_CONTAINS:
                        if wrong_from in message_from.lower():
                            # print('FILTERED F:', message_from)
                            wrong_from_in = True
                            invalid_address += 0.4
                            autoreply += 0.4
                else:
                    pass

            # При наборе остальных признаков отличит автоовет
            if wrong_from_in == False:
                autoreply += 0.2

            if message['Subject'] is not None:
                message_subject = header_parser.header_parse(message, 'Subject')
                if message_subject is not None:
                    for wrong_subject_part in WRONG_SUBJECTS_CONTAINS:
                        if wrong_subject_part.lower() in message_subject.lower():
                            # print('FILTERED S:', message_subject)
                            invalid_address += 0.4
                            autoreply += 0.4
                else:
                    pass

            for wrong_header_wval in WRONG_HEADERS_VALS:
                hname, hval = wrong_header_wval
                if message[hname] is not None:
                    hfiltered = header_parser.header_parse(message, hname)
                    if hfiltered is not None:
                        if hval in hfiltered:
                            # print('FILTERED H:', hname, ' ==> ', hfiltered)
                            invalid_address += 0.2
                            autoreply += 0.2

            #print(autoreply)
            #print(invalid_address)
            if autoreply >= 0.8 and autoreply > invalid_address:
                go_next = True

            size_limit_exceed = False

            if invalid_address >= 0.8:
                for limit_header_wval in LIMIT_EXCEED_HEADERS_VALS:
                    hname, hval = limit_header_wval
                    if message[hname] is not None:
                        hfiltered = header_parser.header_parse(message, hname)
                        if hfiltered is not None:
                            if hval in hfiltered:
                                size_limit_exceed = True

                if size_limit_exceed == True:
                    go_next = True


                else:
                    invalid_list = []
                    address_list = []

                    for part in message.walk():
                        payload = part.get_payload(decode=True)
                        if payload is not None:
                            # + text/html
                            if part.get_content_type() == 'text/plain':
                                charset = part.get_content_charset(failobj=None)
                                if charset is not None:
                                    try:
                                        decoded_part = payload.decode(str(charset), "ignore")
                                    except LookupError:
                                        print('FAIL: unknown charset')
                                        decoded_part = payload.decode()
                                else:
                                    decoded_part = str(payload)

                                if decoded_part is None:
                                    continue

                                for text in LIMIT_EXCEED_TEXT:
                                    if text in decoded_part:
                                        size_limit_exceed = True
                                        go_next = True
                                        break

                                if size_limit_exceed == True:
                                    break

                                address_list = re.findall(r'[\w\.-]+@[\w\.-]+', decoded_part)

                                for address in address_list:
                                    address = address.strip('<>')
                                    daemon_address = False

                                    for wrong_from in WRONG_FROM_CONTAINS:
                                        if wrong_from in address:
                                            daemon_address = True

                                    if address != os.environ.get(
                                            'EMAIL') and not daemon_address and address not in invalid_list:
                                        invalid_list.append(address)
                    '''
                    addr_f = open('res/invalid.txt', 'a')
                    for address in invalid_list:
                        addr_f.write(address + '\n')
                    addr_f.close()
                    '''
                    EmailAddress.objects.create(address=address, limit_exceed_chance=0, detected_spam_chance=0)

                    go_next = True

            if go_next:
                continue

            parts = []
            parsed_html = None
            parsed_plain = None
            message_type = 1

            in_reply_to_header = header_parser.header_parse(message, 'In-Reply-To')
            if in_reply_to_header is not None:
                in_reply_to_header = re.search(r'<.+@eljur.ru>', in_reply_to_header)
                if in_reply_to_header is not None:
                    in_reply_to_header = in_reply_to_header.group()[1:-10]
                    if in_reply_to_header[3:9] == 'message':
                        message_type = 0
                else:
                    in_reply_to_header = ''
            else:
                in_reply_to_header = ''

            # message_from is not None!!!
            message_object = Message(msg_from=message_from, subject=message_subject, in_reply_to_header=in_reply_to_header, type=message_type)

            for part in message.walk():

                payload = part.get_payload(decode=True)
                if payload is not None:

                    charset = part.get_content_charset(failobj=None)

                    if charset is None:
                        decoded_part = str(payload)
                    else:
                        try:
                            decoded_part = payload.decode(str(charset), "ignore")
                        except LookupError:
                            print('FAIL: unknown charset')
                            decoded_part = payload.decode()

                    header_content_disposition = header_parser.header_parse(part, 'Content-Disposition')

                    attachment_part = False

                    if part.get_filename() is not None or header_content_disposition == 'attachment':
                        attachment_part = True
                        if part.get_filename() is not None:
                            file_name = email.header.decode_header(part.get_filename())
                        else:
                            try:
                                file_format = '.' + part.get_subtype()
                                print('GET_SUBTYPE: ' + file_format)
                            except:
                                file_format = ''
                            file_name = '1' + file_format
                        if isinstance(file_name[0][0], str):
                            #file_path = 'res/html/' + msg_num + '_' + (file_name[0][0])
                            file_name = file_name[0][0]
                        else:
                            try:
                                #file_path = 'res/html/' + msg_num + '_' + file_name[0][0].decode(file_name[0][1])
                                file_name = file_name[0][0].decode(file_name[0][1])
                            except:
                                try:
                                    file_format = '.' + part.get_subtype()
                                    print('GET_SUBTYPE: ' + file_format)
                                except:
                                    file_format = ''
                                #file_path = 'res/html/' + msg_num + '_' + ('1') + file_format
                                file_name = '1' + file_format

                        print("!!!!!!!!!")
                        '''
                        m = hashlib.md5()
                        m.update(payload)


                        file_path = ''
                        for i in m.hexdigest():
                            file_path += i + '/'


                        os.makedirs('res/html/'+file_path, exist_ok=True)

                        fp = open('res/html/'+file_path+file_name, 'wb')
                        fp.write(payload)
                        fp.close()
                        '''

                        message_object.save()
                        at = Attachment()
                        at.message = message_object
                        at.file.save(str(message_object.id)+'_'+file_name, ContentFile(payload))


                    if decoded_part is not None:
                        try:
                            if part.get_content_type() == 'text/plain' and attachment_part == False:
                                #decoded_part = '<pre>' + decoded_part.strip() + '</pre>'
                                decoded_part = decoded_part.strip()
                                parts.append(decoded_part.strip())
                                signal.signal(signal.SIGALRM, parse_timeout_signal_handler)
                                signal.alarm(10)
                                try:
                                    parsed_plain = parser.parse(decoded_part)
                                    signal.alarm(0)
                                except Exception:
                                    print("Error: Time Out")
                                    continue


                        except TypeError:
                            print('FAIL: TypeError')
                            try:
                                parts.append(decoded_part.decode())
                            except:
                                pass

                        try:
                            if part.get_content_type() == 'text/html' and attachment_part == False:
                                parts.append(decoded_part)
                                signal.signal(signal.SIGALRM, parse_timeout_signal_handler)
                                signal.alarm(40)
                                try:
                                    parsed_html = parser.parse_html(decoded_part)
                                    signal.alarm(0)
                                except Exception:
                                    print("Error: Time Out")
                                    continue
                        except TypeError:
                            print('FAIL: TypeError')
                            try:
                                parts.append(decoded_part.decode())
                            except:
                                pass

            if not len(parts):
                print('FILTERED: no correct parts')
                continue

            print('OK: ' + msg_num)

            with open('res/html/' + msg_num + '.html', 'w+') as f:
                if charset is None:
                    charset = 'utf-8'
                f.write('<meta charset="' + 'utf-8' + '">')

                for part in parts:
                    if isinstance(part, str):
                        f.write(part)
                        f.write('\n\n<br /><br /><br /><br />\n\n')
                f.write('<br>________________________________________________________________________________')
                if message['Subject'] is not None:
                    f.write(
                        '<br>Subject: ' + str(email.header.make_header(email.header.decode_header(message['Subject']))))
                    f.write('\n\n<br /><br /><br /><br />\n\n')
                # f.write('<br>'+str(type_of_message)+'<br>')
                f.write('________________________________________________________________________________<br>\n')
                if parsed_html == None:
                    if parsed_plain != None:

                        message_object.text = parsed_plain[0]

                        f.write(parsed_plain[0])
                        if parsed_plain[2] == 0:

                            message_object.quote = parsed_plain[1]

                            f.write(
                                '<br>________________________________________________________________________________<br>\n')
                            f.write(parsed_plain[1])
                        message_object.save()
                else:
                    f.write(parsed_html[0])
                    message_object.text = parsed_html[0]
                    if parsed_html[2] == 0:
                        message_object.quote = parsed_html[1]
                        f.write(
                            '<br>________________________________________________________________________________<br>\n')
                        f.write('<blockquote>' + parsed_html[1] + '</blockquote>')
                    message_object.save()