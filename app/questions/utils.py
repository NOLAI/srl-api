from html.parser import HTMLParser
from io import StringIO


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()
    
def strip_html(html: str) -> str:
    s = HTMLStripper()
    s.feed(html)
    return s.get_data()


def split_lang(text: str) -> dict:
    text = text.replace('\n', ' ').replace('\r', ' ').strip()
    result = {'en': text, 'nl': text}
    if '{mlang}' in text:
        if '{mlang en}' in text:
            result['en'] = text.split('{mlang en}')[1].split('{mlang}')[0].strip()
        if '{mlang nl}' in text:
            result['nl'] = text.split('{mlang nl}')[1].split('{mlang}')[0].strip()
    return result