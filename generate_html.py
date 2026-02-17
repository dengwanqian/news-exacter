from database import NewsDatabase
from jinja2 import Template
import datetime

import datetime

# 连接数据库
db = NewsDatabase("news.db")

# 获取所有新闻
news_list = db.get_all_news()

# 过滤近两周内的新闻
two_weeks_ago = datetime.datetime.now() - datetime.timedelta(weeks=2)
filtered_news = []

for news in news_list:
    publish_time_str = news[3]  # 新闻发布时间
    if publish_time_str:
        try:
            # 尝试解析发布时间
            publish_time = datetime.datetime.strptime(publish_time_str[:10], "%Y-%m-%d")
            if publish_time >= two_weeks_ago:
                filtered_news.append(news)
        except:
            # 如果发布时间解析失败，跳过时间检查
            filtered_news.append(news)
    else:
        # 如果没有发布时间，跳过时间检查
        filtered_news.append(news)

print(f"总共 {len(news_list)} 条新闻，过滤后保留 {len(filtered_news)} 条近两周内的新闻")
news_list = filtered_news

# 关闭数据库连接
db.close()

# 转换为字典列表，便于模板渲染
news_data = []
for news in news_list:
    news_data.append({
        "id": news[0],
        "title": news[1],
        "author": news[2],
        "publish_time": news[3],
        "source": news[4],
        "content": news[5],
        "summary": news[6],
        "url": news[7],
        "created_at": news[8]
    })

# 读取模板文件
with open("template.html", "r", encoding="utf-8") as f:
    template_content = f.read()

# 渲染模板
template = Template(template_content)
html_content = template.render(news_list=news_data)

# 保存生成的HTML
output_file = f"news(2 weeks)_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML页面已生成: {output_file}")