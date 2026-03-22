from config import NEWS_SOURCES, DB_PATH, SELENIUM_TIMEOUT,FILTER_KEYWORDS
from news_extractor import NewsExtractor
from database import NewsDatabase
import time

import datetime
from logger import info, debug, error, warning



def main():
    # 初始化数据库
    db = NewsDatabase(DB_PATH)

    
    # 初始化新闻提取器
    extractor = NewsExtractor(timeout=SELENIUM_TIMEOUT)
    
    # 初始化链接缓存，使用有序字典来维护最近使用的链接
    from collections import OrderedDict
    import json
    import os
    
    CACHE_FILE = "link_cache.json"
    MAX_CACHE_SIZE = 2000
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
    
    try:
        # 遍历所有信息来源
        for source_item in NEWS_SOURCES:
            source_url = source_item["url"]
            source_name = source_item["source"]
            print(f"处理信息来源: {source_name} ({source_url})")
            info(f"处理信息来源: {source_name} ({source_url})")

            news_links=[]
            if source_url.startswith("https://mp.weixin.qq.com/cgi-bin/appmsgpublish"):
                # 从URL中提取fakeid
                fakeid = source_url.split("fakeid=")[1]

                # 调用get_articles获取文章链接
                count=5
                if source_name == "中国青年报":
                    count=10
                news_links = extractor.get_article_links(fakeid=fakeid, begin=0, count=count)
            else:
                # 获取渲染后的页面
                page_source = extractor.get_rendered_page(source_url)
                if not page_source:
                    continue
                
                # 提取新闻链接
                news_links = extractor.extract_news_links(page_source, source_url)
            print(f"提取到 {len(news_links)} 条新闻链接")

            
            # 遍历新闻链接，提取内容
            for link in news_links[:20]:  # 限制每次处理的新闻数量
                print(f"处理新闻: {link}")


                
                # 检查链接是否在缓存中
                if link in link_cache:
                    print(f"链接已处理过，跳过: {link}")
                    # 更新缓存中的位置（移到末尾表示最近使用）
                    link_cache.move_to_end(link)
                    continue
                
                # 将链接添加到缓存
                link_cache[link] = True
                # 如果缓存超过最大大小，删除最旧的链接
                if len(link_cache) > MAX_CACHE_SIZE:
                    link_cache.popitem(last=False)
                
                print(f"链接加入缓存，当前缓存大小: {len(link_cache)}")
                
                # 获取渲染后的新闻页面
                news_page = extractor.get_rendered_page(link)
                if not news_page:
                    continue
                
                # 提取新闻内容
                news_data = extractor.extract_news_content(news_page, link)
                if not news_data:
                    continue
                
                # 0. 检查标题是否已存在（在生成摘要前检查，避免不必要的API调用）
                if db.is_title_exists(news_data["title"]):
                    print(f"标题已存在，跳过: {news_data['title']}")
                    continue
                
                # 1. 检查内容是否包含指定关键词
                content = news_data["content"]+news_data["title"]
                keywords = FILTER_KEYWORDS
                has_keyword = any(keyword in content for keyword in keywords)
                if not has_keyword:
                    print(f"新闻内容不包含指定关键词，跳过: {news_data['title']}")
                    continue
                
                # 2. 检查发布时间是否在一周内
                publish_time_str = news_data["publish_time"]
                current_time = datetime.datetime.now()
                
                one_week_ago = current_time - datetime.timedelta(weeks=1)
                two_weeks_ago = current_time - datetime.timedelta(weeks=2)

                period_start = one_week_ago
                
                
                try:
                    # 尝试解析发布时间
                    if publish_time_str:
                        # 简单的日期解析，可能需要根据实际格式调整
                        publish_time = datetime.datetime.strptime(publish_time_str[:10], "%Y-%m-%d")
                        if publish_time < period_start:
                            print(f"新闻发布时间超过{period_start}，跳过: {news_data['title']}")
                            continue
                except:
                    # 如果发布时间解析失败，跳过时间检查
                    pass
                
                # 生成内容摘要（现在只有标题不存在时才会调用AI生成摘要）
                summary = extractor.summarize_content(news_data["content"])
                
                # 使用百度智能云NLP分类API获取分类
                # 传递标题和内容作为参数
                category, subcategory = extractor.classify_content(news_data["title"], summary)
                               
                # 保存到数据库，使用配置中的source名称
                success = db.insert_news(
                    title=news_data["title"],
                    author=news_data["author"],
                    publish_time=news_data["publish_time"],
                    source=source_name,  # 使用配置中的source名称
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
                
                time.sleep(1)  # 避免请求过快
        
    
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
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