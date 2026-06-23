import re 
from lxml.html import HtmlElement
from gne_local.defaults import AUTHOR_PATTERN


class AuthorExtractor:
    def __init__(self):
        self.author_pattern = AUTHOR_PATTERN

    def extractor(self, element: HtmlElement):
        # 优先查找 id="js_author_name_text" 的 span 标签
        author_spans = element.xpath('.//span[@id="js_author_name_text"]/text()')
        print(f'author_spans: {author_spans}')
        if author_spans:
            author = author_spans[0].strip()
            if author:
                print(f'author: {author}')
                return author
            else:
                print('author tag is empty')
        
        # 回退到正则匹配
        text = ''.join(element.xpath('.//text()'))
        for pattern in self.author_pattern:
            author_obj = re.search(pattern, text)
            if author_obj:
                return author_obj.group(1)
        return ''
