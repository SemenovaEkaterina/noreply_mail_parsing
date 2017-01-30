import imaplib
import parser
imaplib._MAXLINE = 2000000
import email
import os
import sys
import re
import header_parser

mail = imaplib.IMAP4_SSL('imap.gmail.com')

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
    ('X-MS-Exchange-Message-Is-Ndr', '') #              ?
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

min_id = os.environ.get('MIN_ID', 144000)
max_id = os.environ.get('MAX_ID', 145000)

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
    r = open('res/full_messages/'+str(msg_num)+'.txt', 'w+')
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

    # разделить multipart/report и delivery-status по вероятностям
    # error -> text/plain
    if message.get_content_type() == 'multipart/report':
        for param in message.get_params(failobj=[]):
            if param[0] == 'report-type' and param[1] == 'delivery-status':
                invalid_address += 0.4

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
            # print(message_subject)
            for wrong_subject_part in WRONG_SUBJECTS_CONTAINS:
                if wrong_subject_part in message_subject:
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

        # поиск по телу письма в text/plain, если пуст, то text/html

        if size_limit_exceed == True:
            go_next = True
            break


        invalid_list = []
        address_list = []

        for part in message.walk():
            # + text/html
            if part.get_content_type() == 'text/plain':
                charset = part.get_content_charset(failobj=None)
                if charset is not None:
                    decoded_part = part.get_payload(decode=True).decode(str(charset), "ignore")
                    address_list = re.findall(r'[\w\.-]+@[\w\.-]+', decoded_part)
                # else:
                #    decoded_part = part.get_payload(decode=True)

                for address in address_list:
                    address = address.strip('<>')
                    valid_address = True

                    for wrong_from in WRONG_FROM_CONTAINS:
                        if wrong_from in address:
                            valid_address = False

                    if address != os.environ.get('EMAIL') and valid_address and address not in invalid_list:
                        invalid_list.append(address)

        addr_f = open('res/invalid.txt', 'a')
        for address in invalid_list:
            addr_f.write(address + '\n')
        addr_f.close()

        go_next = True

    if go_next:
        continue

    parts = []
    parsed_html = ''
    parsed_plain = ''
    type_of_message = 1

    for part in message.walk():

        charset = part.get_content_charset(failobj=None)

        if charset is None:
            decoded_part = part.get_payload(decode=True)
        else:
            try:
                payload = part.get_payload(decode=True)
                if payload is not None:
                    decoded_part = part.get_payload(decode=True).decode(str(charset), "ignore")
                else:
                    decoded_part = None
            except LookupError:
                print('FAIL: unknown charset')
                decoded_part = part.get_payload(decode=True).decode()

        header_content_disposition = header_parser.header_parse(part, 'Content-Disposition')

        if part.get_filename() is not None or header_content_disposition == 'attachment':
            if part.get_filename() is not None:
                file_name = email.header.decode_header(part.get_filename())
            else:
                file_name = '1'
            if isinstance(file_name[0][0], str):
                file_path = 'res/html/' + msg_num + '_' + (file_name[0][0])
            else:
                try:
                    file_path = 'res/html/'+msg_num+'_'+file_name[0][0].decode(file_name[0][1])
                except:
                    file_path = 'res/html/'+msg_num+'_'+('1')
            fp = open(file_path, 'wb')
            payload = part.get_payload(decode=True)
            if payload is not None:
                fp.write(part.get_payload(decode=True))
            fp.close()

        if decoded_part is not None:
            try:
                if part.get_content_type() == 'text/plain':
                    parsed_plain, type_of_message = parser.parse(decoded_part)
                    decoded_part = '<pre>' + decoded_part.strip() + '</pre>'
                parts.append(decoded_part.strip())
            except TypeError:
                #print('FAIL: TypeError')
                try:
                    parts.append(decoded_part.decode())
                except:
                    pass

            try:
                if part.get_content_type() == 'text/html' and part.get_filename() is None:
                    parsed_html, type_of_message = parser.parse_html(decoded_part)
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
        f.write('<meta charset="'+str(charset)+'">')

        for part in parts:
            if isinstance(part, str):
                f.write(part)
                f.write('\n\n<br /><br /><br /><br />\n\n')
        f.write('________________________________________________________________________________')
        if message['Subject'] is not None:
            f.write('<br>Subject: ' + str(email.header.make_header(email.header.decode_header(message['Subject']))))
            f.write('\n\n<br /><br /><br /><br />\n\n')
        f.write('<br>'+str(type_of_message)+'<br>')
        if parsed_html == '':
            f.write(parsed_plain)
        else:
            f.write(parsed_html)
