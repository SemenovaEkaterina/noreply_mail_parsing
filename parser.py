import re
from html.parser import HTMLParser

'''
class TextFromHTML(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.text = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.text += ' ' + attr[1] + ' - '
        if tag == 'br'or tag == 'br /' or tag == 'div' or tag == 'p':
            self.text += '\n'

    def handle_endtag(self, tag):
        if tag == 'div' or tag == 'p':
            self.text += '\n'

    def handle_data(self, data):
        self.text += data
'''


# Add '\n'
class HTML(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.text = ''

    def handle_starttag(self, tag, attrs):
        self.text += '<' + tag
        for attr in attrs:
            self.text += ' ' + attr[0] + '="' + attr[1] + '" '
        self.text += '>'
        if tag != 'a' and tag != 'span':
            self.text += '\n'

    def handle_endtag(self, tag):
        self.text += '</' + tag + '>'
        if tag != 'a' and tag != 'span':
            self.text += '\n'

    def handle_data(self, data):
        self.text += data


quote_pattern = re.compile(r'[^\n]+ написала?.?вам.?сообщение.?в.+Электронном.+журнале.+школы.*№.+:.*'
                             r'Это.+автоматическое.+уведомление,.+и.+на.+него.+не.+следует.+отвечать\..+'
                             r'Чтобы.+ответить.+отправителю,.+войдите.+в.+Электронный.+журнал.+https://.+\.eljur\.ru',
                           re.DOTALL)

pre_patterns = [
    (re.compile(r' {2,}'), ' '),
    (re.compile(r'\t{2,}'), '\t'),
    (re.compile(r'\n \n'), '\n'),
    (re.compile(r'^ '), ''),
    (re.compile(r'\n\t\n'), '\n')
]

post_patterns = [
    (re.compile(r'\n.+20\d\d ?г., \d{1,2}:\d\d пользователь.+<.+@.+\..+> ?[\n]?написал:.+\n'), '\n'),
    (re.compile(r'\n.+[П,п]ользователь.+Электронный журнал.+[\n]?написал.+\n'), '\n'),
    (re.compile(r'\n\d\d\.\d\d\.20\d\d \d?\d:\d\d, Электронный журнал.*[\n]?пишет:.*\n'), '\n'),
    (re.compile(r'\n.+Электронный журнал.+noreply@eljur.ru.*\n'), '\n'),
    (re.compile(r'\n.+ 20\d\d ?г?\.?,? \d?\d:\d\d .+ от Электронный журнал .+noreply@eljur.ru.+:.+\n'), '\n'),
    #(re.compile(r'\n.+-------- Исходное сообщение --------.+[\n]+Дата: .+[\n]+Кому: .+[\n]+Тема: .+\n'), '\n'),
    (re.compile('\n ?Отправлено с[о]? .+\n'), '\n'),
    (re.compile(r'\n ?Отправлено из .+\n'), '\n'),
    (re.compile(r'\n-- ?\n'), '\n'),
    (re.compile(r'\n{2,}'), '\n')
]

def parse_html(html):
    my_parser = HTML()
    my_parser.feed(html)
    return parse(my_parser.text)


# 0 - удалось выделить цитату; 1 - нет
def parse(text):
    text = '\n'+text+'\n'

    for pattern in pre_patterns:
        text = pattern[0].sub(pattern[1], text)

    new_text = re.sub(quote_pattern, '\n', text)
    if len(new_text) == len(text):
        return text, 1

    text = new_text
    for pattern in post_patterns:
        text = re.sub(pattern[0], pattern[1], text)

    return text, 0
