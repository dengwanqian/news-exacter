from config import NEWS_SOURCES, DB_PATH, SELENIUM_TIMEOUT,FILTER_KEYWORDS
from news_extractor import NewsExtractor
from database import NewsDatabase
import time

import datetime



def main():
    # 初始化数据库
    db = NewsDatabase(DB_PATH)

    
    # 初始化新闻提取器
    extractor = NewsExtractor(timeout=SELENIUM_TIMEOUT)
    
    try:
        # 遍历所有信息来源
        for source_item in NEWS_SOURCES:
            source_url = source_item["url"]
            source_name = source_item["source"]
            print(f"处理信息来源: {source_name} ({source_url})")
            
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
                content = news_data["content"]
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
                
                # 保存到数据库，使用配置中的source名称
                success = db.insert_news(
                    title=news_data["title"],
                    author=news_data["author"],
                    publish_time=news_data["publish_time"],
                    source=source_name,  # 使用配置中的source名称
                    content=news_data["content"],
                    summary=summary,
                    url=news_data["url"]
                )
                
                if success:
                    print(f"成功保存新闻: {news_data['title']}")
                else:
                    print(f"新闻已存在或保存失败: {news_data['title']}")
                
                time.sleep(1)  # 避免请求过快
    
    except Exception as e:
        print(f"程序执行出错: {e}")
        e.print_exc()
        
    finally:
        # 关闭资源
        extractor.close()
        db.close()
        print("程序执行完毕")

if __name__ == "__main__":
    main()