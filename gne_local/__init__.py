from lxml.html import fromstring
from .utils import pre_parse, remove_noise_node, config
from gne_local.extractor import ContentExtractor, TitleExtractor, TimeExtractor, AuthorExtractor, SourceExtractor


class GeneralNewsExtractor:
    def extract(self, html, title_xpath='', host='', noise_node_list=None, with_body_html=False):
        # 在 normalize 之前先用原始 HTML 提取作者，避免 normalize_node 误删 span 标签（如微信公众号的 js_author_name_text）
        raw_element = fromstring(html)
        author = AuthorExtractor().extractor(raw_element)

        element = pre_parse(html)
        remove_noise_node(element, noise_node_list)
        content = ContentExtractor().extract(element, host, with_body_html)
        title = TitleExtractor().extract(element, title_xpath=title_xpath)
        publish_time = TimeExtractor().extractor(element)
        source = SourceExtractor().extractor(element)
        result = {'title': title,
                  'author': author,
                  'publish_time': publish_time,
                  'source': source,                  
                  'content': content[0][1]['text'],
                  'images': content[0][1]['images']}
        if with_body_html or config.get('with_body_html', False):
            result['body_html'] = content[0][1]['body_html']
        return result
