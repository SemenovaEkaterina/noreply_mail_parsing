import imaplib
import sys
import os
SEARCH_FOLDER = 'Trash'
imaplib._MAXLINE = 2000000

def make_message_list(search_criteria):
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
        res, data = mail.search(None, search_criteria)
    except imaplib.IMAP4.error:
        sys.exit(1)

    print('OK: received a list of messages')

    if len(data) > 0:
        message_ids = data.pop().split()
    else:
        message_ids = []

    return message_ids, mail