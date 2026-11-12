import random

from config import NEWS_SOURCES, DB_PATH, SELENIUM_TIMEOUT,FILTER_KEYWORDS
from news_extractor import NewsExtractor
from database import NewsDatabase
import time
import datetime
import json
import os
import traceback
from collections import OrderedDict
from logger import info, debug, error, warning

CACHE_FILE = "link_cache.json"
MAX_CACHE_SIZE = 2000


def load_link_cache():
    # 初始化链接缓存，使用有序字典来维护最近使用的链接
    link_cache = OrderedDict()

    # 从文件加载缓存
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached_links = json.load(f)
                # 将加载的链接添加到OrderedDict
                for link in cached_links:
                    link_cache[link] = True
                # 如果缓存超过最大大小，删除最旧的链接
                while len(link_cache) > MAX_CACHE_SIZE:
                    link_cache.popitem(last=False)
                print(f"从文件加载缓存，当前缓存大小: {len(link_cache)}")
        except Exception as e:
            print(f"加载缓存失败: {e}")
            error(f"加载缓存失败: {e}", "cache")
            link_cache = OrderedDict()
    else:
        print("缓存文件不存在，创建新缓存")
        info("缓存文件不存在，创建新缓存", "cache")

    return link_cache


def process_link(extractor, db, link_cache, link, source_name):
    """处理单条新闻链接：抓详情页、抽取正文、过滤、摘要、分类并入库

    意外错误直接抛出，由调用方按链接捕获，避免一条链接的异常中断该来源剩余链接。
    """
    author=""

    if type(link) != str: #特殊处理
        author=link["author"]
        link=link["url"]
    # 检查链接是否在缓存中
    if link in link_cache:
        print(f"链接已处理过，跳过: {link}")
        # 更新缓存中的位置（移到末尾表示最近使用）
        link_cache.move_to_end(link)
        return

    # 将链接添加到缓存
    link_cache[link] = True
    # 如果缓存超过最大大小，删除最旧的链接
    if len(link_cache) > MAX_CACHE_SIZE:
        link_cache.popitem(last=False)

    print(f"链接加入缓存，当前缓存大小: {len(link_cache)}")

    # 获取渲染后的新闻页面
    news_page = extractor.get_rendered_page(link)
    if not news_page:
        return

    # 提取新闻内容
    #等待一段时间
    #获取2到4秒的随机时间
    seconds= random.uniform(2, 4)
    time.sleep(seconds)
    news_data = extractor.extract_news_content(news_page, link)
    if not news_data:
        return
    if author: # 列表页中有作者信息，覆盖提取到的作者信息
        if "学院" in author or "学校" in author:
            return
        elif "大学"  in author:
            news_data["source"]=author
        else:
            news_data["author"]=author
    if news_data["author"]:
        if "学院" in news_data["author"] or "学校" in news_data["author"]:
            return
    if news_data["source"]:
        if "学院" in news_data["source"] or "学校" in news_data["source"]:
            return
    if news_data["title"]:
        title=news_data["title"]
        if "中学" in title or "小学" in title or "幼" in title or "县" in title:
            return
    # 0. 检查标题是否已存在（在生成摘要前检查，避免不必要的API调用）
    if db.is_title_exists(news_data["title"]):
        print(f"标题已存在，跳过: {news_data['title']}")
        return

    # 1. 检查内容是否包含指定关键词
    content = news_data["content"]+news_data["title"]
    keywords = FILTER_KEYWORDS
    has_keyword = any(keyword in content for keyword in keywords)
    if not has_keyword:
        print(f"新闻内容不包含指定关键词，跳过: {news_data['title']}")
        return

    # 2. 检查发布时间是否在一周内
    publish_time_str = news_data["publish_time"]
    current_time = datetime.datetime.now()

    one_week_ago = current_time - datetime.timedelta(weeks=1)
    two_weeks_ago = current_time - datetime.timedelta(weeks=2)

    period_start = one_week_ago
    #period_start = two_weeks_ago

    try:
        # 尝试解析发布时间
        if publish_time_str:
            # 简单的日期解析，可能需要根据实际格式调整
            publish_time = datetime.datetime.strptime(publish_time_str[:10], "%Y-%m-%d")
            if publish_time < period_start:
                print(f"新闻发布时间超过{period_start}，跳过: {news_data['title']}")
                return
    except:
        # 如果发布时间解析失败，跳过时间检查
        pass

    # 生成内容摘要
    summary = extractor.summarize_content(news_data["content"])
    if source_name == "中国教育信息化网" or source_name == "北京市政府官网-北京要闻":
        if "中学" in summary or "小学" in summary or "幼儿" in summary or "中心学校" in summary or "基础教育" in summary:
            return

    # 使用百度智能云NLP分类API获取分类
    # 传递标题和内容作为参数
    category, subcategory = extractor.classify_content(news_data["title"], summary)
    if "category" in news_data and news_data["category"]!="":
        category = news_data["category"]

    # 保存到数据库，使用配置中的source名称(如果source为空)
    source = news_data["source"]
    if source=="":
        source = source_name
    print(f"保存新闻: {source}")
    success = db.insert_news(
        title=news_data["title"],
        author=news_data["author"],
        publish_time=news_data["publish_time"],
        source=source,  
        content=news_data["content"],
        summary=summary,
        url=news_data["url"],
        category=category,
        subcategory=subcategory
    )

    if success:
        print(f"成功保存新闻: {news_data['title']}")
        info(f"成功保存新闻: {news_data['title']}", "database")
    else:
        print(f"新闻已存在或保存失败: {news_data['title']}")
        warning(f"新闻已存在或保存失败: {news_data['title']}", "database")

    time.sleep(3)  # 避免API请求过快触发限流


def process_source(extractor, db, link_cache, source_item):
    """处理单个信息来源：抓列表页、提取新闻链接，再逐条交给process_link

    意外错误直接抛出，由调用方按来源捕获，避免一个来源的异常中断后面的来源。
    """
    source_url = source_item["url"]
    source_name = source_item["source"]
    print(f"处理信息来源: {source_name} ({source_url})")
    info(f"处理信息来源: {source_name} ({source_url})")

    news_links=[]
    if source_url.startswith("https://mp.weixin.qq.com/cgi-bin/appmsgpublish"):
        print(f"微信公众号信息现在不可搜，略过。")
        return  # 跳过微信公众号,因为公众号功能变化，无法获取文章链接了。
        '''
        # 从URL中提取fakeid
        fakeid = source_url.split("fakeid=")[1]

        # 调用get_articles获取文章链接
        count=5
        if source_name == "中国青年报":
            count=10
        news_links = extractor.get_article_links(fakeid=fakeid, begin=0, count=count)
        '''
    else:
        # 获取渲染后的页面
        page_source = extractor.get_rendered_page(source_url)
        if not page_source:
            return

        # 提取新闻链接
        news_links = extractor.extract_news_links(page_source, source_url) or []
    if news_links:
        info(f"提取到 {len(news_links)} 条新闻链接")
    else:
        info(f"未提取到新闻链接，跳过该信息来源: {source_name}")
        return

    # 遍历新闻链接，提取内容
    for link in news_links[:50]:  # 限制每次处理的新闻数量
        print(f"处理新闻: {link}")
        try:
            process_link(extractor, db, link_cache, link, source_name)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"处理新闻失败，跳过: {link} -> {e}")
            error(f"处理新闻失败，跳过: {link} 报错: {e}")
            error(traceback.format_exc())
            # 失败同样保持限速，避免请求过快触发限流
            time.sleep(3)


def main():
    # 初始化数据库
    db = NewsDatabase(DB_PATH)

    # 初始化新闻提取器
    extractor = NewsExtractor(timeout=SELENIUM_TIMEOUT)

    link_cache = load_link_cache()

    try:
        # 遍历所有信息来源
        for source_item in NEWS_SOURCES:
            try:
                process_source(extractor, db, link_cache, source_item)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                source_name = source_item["source"]
                print(f"处理信息来源出错，跳过该来源: {source_name} -> {e}")
                error(f"处理信息来源出错，跳过该来源: {source_name} ({source_item['url']}) 报错: {e}")
                error(traceback.format_exc())

    except Exception as e:
        print(f"程序执行出错: {e}")
        traceback.print_exc()
        error(f"程序执行出错: {e}")
        error(traceback.format_exc())
        
    finally:
        # 保存缓存到文件
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                # 只保存链接列表
                json.dump(list(link_cache.keys()), f, ensure_ascii=False, indent=2)
            print(f"缓存已保存到文件，当前缓存大小: {len(link_cache)}")
        except Exception as e:
            print(f"保存缓存失败: {e}")
            error(f"保存缓存失败: {e}", "cache")
        # 关闭资源
        extractor.close()
        db.close()
        print("新闻筛选完毕。")
        info("新闻筛选完毕。")


    print("现在开始生成最终分类...")
    info("现在开始生成最终分类...", "classification")
    import classify_existing_news 
    classify_existing_news.main()

if __name__ == "__main__":
    main()
