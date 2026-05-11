import re
from lxml.html import HtmlElement
from gne_local.defaults import SOURCE_PATTERN


class SourceExtractor:
    def __init__(self):
        self.source_pattern = SOURCE_PATTERN

    def extractor(self, element: HtmlElement):
        text = ''.join(element.xpath('.//text()'))
        for pattern in self.source_pattern:
            source_obj = re.search(pattern, text)
            if source_obj:
                return source_obj.group(1)
        return ''
