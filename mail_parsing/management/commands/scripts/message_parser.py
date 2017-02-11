import re
from html.parser import HTMLParser
import html


class TextFromHTML(HTMLParser):
    def __init__(self, charset):
        HTMLParser.__init__(self)
        self.text = ''
        self.style = False
        self.charset = charset

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            self.style = True
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.text += ' ' + attr[1] + ' - '
        if tag == 'br' or tag == 'br /' or tag == 'div' or tag == 'p':
            self.text += '\n'

    def handle_endtag(self, tag):
        if tag == 'style':
            self.style = False
        if tag == 'div' or tag == 'p':
            self.text += '\n'

    def handle_data(self, data):
        if self.style == False:
            try:
                data = html.unescape(data)
            except:
                pass
            self.text += data

    def handle_comment(self, data):
        pass



'''
# for HTML parsing
# Add '\n'
class HTML(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.text = ''
        self.style = False

    def handle_starttag(self, tag, attrs):
        self.text += '<' + tag
        for attr in attrs:
            self.text += ' ' + attr[0] + '="' + attr[1] + '" '
        self.text += '>'
        if tag != 'a' and tag != 'span':
            self.text += '\n'

    def handle_endtag(self, tag):
        if tag != 'br':
            self.text += '</' + tag + '>'
            if tag != 'a' and tag != 'span':
                self.text += '\n'

    def handle_data(self, data):
        self.text += data

    def handle_comment(self, data):
        pass

'''

'''
for HTML parsing
quote_pattern = re.compile(r'(<div[^\n]*>)?[\n]*[^\n]+ написала?.?вам.?сообщение.?в.+Электронном.+журнале.+школы.*№.+:.*'
                             r'Это.+автоматическое.+уведомление,.+и.+на.+него.+не.+следует.+отвечать\..+'
                             r'Чтобы.+ответить.+отправителю,.+войдите.+в.+Электронный.+журнал.+https://.+\.eljur\.ru[\n]?(</a>)?(</div>)?',
                           re.DOTALL)

pre_patterns = [
    (re.compile(r' {2,}'), ' '),
    (re.compile(r'\t{2,}'), '\t'),
    (re.compile(r'\n \n'), '\n'),
    (re.compile(r'^ '), ''),
    (re.compile(r'\n\t\n'), '\n')
]

datetime_patterns = [
    #(re.compile(r'\n(\s*<.+>\s*)*From: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Sent: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*To: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Subject: ?.+(\s*<.+>\s*)*\n'), '\n'),
    (re.compile(r'\n-------- Исходное сообщение --------(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Дата: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Кому: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Тема: ?.+(\s*<.+>\s*)*\n'), '\n'),
    (re.compile(r'От: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Отправлено: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Кому: ?.+(\s*<.+>\s*)*[\n]+(\s*<.+>\s*)*Тема: ?.+(\s*<.+>\s*)*\n'),'\n'),
    (re.compile(r'\n.+20\d\d ?г., \d{1,2}:\d\d пользователь.+<.+@.+\..+> ?[\n]?написал:.+\n'), '\n'),
    (re.compile(r'\n.+[П,п]ользователь.+Электронный журнал.+[\n]?написал.+\n'), '\n'),
    (re.compile(r'\n\d\d\.\d\d\.20\d\d \d?\d:\d\d, Электронный журнал.*[\n]?пишет:.*\n'), '\n'),
    (re.compile(r'\n.+Электронный журнал.+noreply@eljur.ru.*\n'), '\n'),
    (re.compile(r'\nЭлектронный журнал.+noreply@eljur.ru.*20\d\d ?г\..+Сообщение:.*\n'), '\n'),
    (re.compile(r'\n.+ 20\d\d ?г?\.?,? \d?\d:\d\d .+ от Электронный журнал .+noreply@eljur.ru.+:.+\n'), '\n'),
]

post_patterns = [
    (re.compile(r'\n<blockquote.+>(\s*<.+>\s*)*</blockquote>\n'), '\n'),
    (re.compile(r'\n ?Отправлено с[о]? .+\n'), '\n'),
    (re.compile(r'\n ?Отправлено из .+\n'), '\n'),
    (re.compile(r'\n ?Sent from .+\n'), '\n'),
    #(re.compile(r'\n(\s*<.+>\s*)*[^!]--[^>]-? ?(\s*<.+>\s*)*\n'), '\n'),
    (re.compile(r'>?[\s]*---? ?'), '>\n'),
    (re.compile(r'\n> ?\n'), '\n'),
    (re.compile(r'\n{2,}'), '\n'),
    (re.compile(r'\n ?Получите и Вы свой бесплатный электронный адрес на .+\n'), '\n'),
]
'''
quote_patterns = [
    re.compile(r'\n[^\n]+ ?\n?написала?.+вам.+сообщение.+в.+Электронном.+журнале.+школы.*№.+:.*'
                             r'Это.+автоматическое.+уведомление,.+и.+на.+него.+не.+следует.+отвечать\..+'
                             r'Чтобы.+ответить.+отправителю,.+войдите.+в.+Электронный.+журнал.+https://.+\.eljur\.ru',
                           re.DOTALL),
    re.compile(r'Это.+автоматическое.+уведомление,.+и.+на.+него.+не.+следует.+отвечать\..+'
                             r'Чтобы.+ответить.+отправителю,.+войдите.+в.+Электронный.+журнал.+https://.+\.eljur\.ru',
                           re.DOTALL)
]

datetime_patterns = [
    (re.compile(r'\n.*Исходное сообщение.*\n*.*[\n]+Дата: ?.+[\n]+Кому: ?.+[\n]+Тема: ?.+\n'), '\n'),
    (re.compile(r'\nFrom: ?.+Sent: ?.+To: ?.+Subject: ?.+Importance: ?.+\n', re.DOTALL), '\n'),
    (re.compile(r'\nОт: ?.+Отправлено: ?.+Кому: ?.+Тема: ?.+\n', re.DOTALL),'\n'),
    (re.compile(r'\n.+20\d\d ?г., \d{1,2}:\d\d пользователь.+<.+@.+\..+> ?[\n]? ?написал:.+\n'), '\n'),
    (re.compile(r'\n.+[П,п]ользователь.+Электронный журнал.+[\n]? ?написал.+\n'), '\n'),
    (re.compile(r'\n\d\d\.\d\d\.20\d\d \d?\d:\d\d, Электронный журнал.*[\n]? ?пишет:.*\n'), '\n'),
    (re.compile(r'\n.+Электронный журнал.+noreply@eljur.ru.*\n'), '\n'),
    (re.compile(r'\nЭлектронный журнал.+noreply@eljur.ru.*20\d\d ?г\..+Сообщение:.*\n'), '\n'),
    (re.compile(r'\n.+ 20\d\d ?г?\.?,? \d?\d:\d\d .+ от( Электронный журнал)? .+noreply@eljur.ru.+:.*\n'), '\n'),
]

pre_patterns = [
    (re.compile(r' {2,}'), ' '),
    (re.compile(r'\t{2,}'), '\t'),
    (re.compile(r'\n \n'), '\n'),
    (re.compile(r'^ '), ''),
    (re.compile(r'\n\t\n'), '\n')
]

post_patterns = [
    (re.compile(r'\n ?Отправлено с[о]? .+\n'), '\n'),
    (re.compile(r'\n ?Отправлено из .+\n'), '\n'),
    (re.compile(r'\n ?Отправлено через .+\n'), '\n'),
    (re.compile(r'\n.+ ?Sent from .+\n'), '\n'),
    (re.compile(r'\n---? ?\n'), '\n'),
    (re.compile(r'>[\s]*---? ?'), '>\n'),
    (re.compile(r'[\s]*---? ?'), '\n'),
    (re.compile(r'\s*\n'), '\n'),
    (re.compile(r'\n{2,}'), '\n'),
    (re.compile(r'\n ?Получите и Вы свой бесплатный электронный адрес на .+\n'), '\n'),
    (re.compile(r'\n> ?\n'), '\n'),
]


def parse_html(html, charset):
    my_parser = TextFromHTML(charset)
    my_parser.feed(html)
    return parse(my_parser.text)


# 0 - удалось выделить цитату; 1 - нет
def parse(text):
    text = '\n'+text+'\n'

    for pattern in pre_patterns:
        text = pattern[0].sub(pattern[1], text)

    for pattern in quote_patterns:
        quote = re.search(pattern, text)
        if quote is not None:
            current_pattern = pattern
            break

    if quote is not None:
        quote = quote.group()
        text = re.sub(current_pattern, '\n', text)
        has_quote = 0
        for pattern in datetime_patterns:
            datetime = re.search(pattern[0], text)
            if datetime is not None:
                quote = datetime.group() + quote
            text = re.sub(pattern[0], pattern[1], text)

    else:
        has_quote = 1

    for pattern in post_patterns:
        text = re.sub(pattern[0], pattern[1], text)

    return text, quote, has_quote