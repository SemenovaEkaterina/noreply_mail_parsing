import email


def header_parse(message, header_name):
    try:
        header = email.header.make_header(email.header.decode_header(message[header_name]))
        return str(header)
    except:
        header = message.__getitem__(header_name)
        if header is not None:
            return header
        else:
            return None
