import imaplib
import os
SEARCH_FOLDER = 'Trash'
imaplib._MAXLINE = 3000000


def make_message_list(search_criteria):
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
    except:
        return [], None, 'ERROR: failed to connect'

    email_addres = os.environ.get('EMAIL', '')
    password = os.environ.get('PASSWORD', '')

    try:
        mail.login(email_addres, password)
    except imaplib.IMAP4.error:
        return [], mail, 'ERROR: login error'

    try:
        res, folders = mail.list()
    except imaplib.IMAP4.error:
        return [], mail, 'ERROR: failed to get folders'

    found_folder = False
    for folder in folders:
        if SEARCH_FOLDER in str(folder):
            found_folder = folder

    if found_folder is None:
        return [], mail, 'ERROR: failed to find a folder'

    folder_name = [x for x in str(found_folder).split('"') if 'Gmail' in x].pop()

    # "INBOX"
    # folder_name = [x for x in str(found_folder).split('"')][-2]

    try:
        res, sel_data = mail.select(folder_name)
    except imaplib.IMAP4.error:
        return [], mail, 'ERROR: failed to select a folder'

    # print('OK: selected folder, message counter:', int(sel_data.pop()))

    try:
        res, data = mail.search(None, search_criteria)
    except imaplib.IMAP4.error:
        return [], mail, 'ERROR: failed to get list of message'

    if len(data) > 0:
        message_ids = data.pop().split()
    else:
        message_ids = []

    return message_ids, mail, 'OK'