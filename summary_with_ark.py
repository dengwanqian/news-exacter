import datetime
import os
from openai import OpenAI

from openai import OpenAI
import os
from dotenv import load_dotenv

from database import NewsDatabase

# 加载环境变量（把API Key存.env，不要硬编码）
load_dotenv()
api_key = os.getenv('ARK_API_KEY')

# 初始化客户端（兼容OpenAI格式）
client = OpenAI(
    api_key=api_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

#从数据库中获取新闻
db = NewsDatabase("news.db")
news_list = db.get_all_news_with_undecided(limit=200)
news_list = sorted(news_list, key=lambda x: x[3], reverse=True)

one_weeks_ago = datetime.datetime.now() - datetime.timedelta(weeks=1)

for news in news_list:
    article = news[5]
    id = news[0]

    publish_time_str = news[3]  # 新闻发布时间
    if publish_time_str:
        try:
            # 尝试解析发布时间
            publish_time = datetime.datetime.strptime(publish_time_str[:10], "%Y-%m-%d")
            if publish_time < one_weeks_ago:
                continue
        except:
            # 如果发布时间解析失败，跳过时间检查
            continue

    # 调用API生成摘要
    response = client.chat.completions.create(
        model="doubao-seed-2-0-pro-260215",  # 模型ID，可在方舟控制台查看
        messages=[
            {"role": "system", "content": "你是一个专业的文本摘要助手，用简洁、通顺的中文生成文章摘要，保留核心信息和关键结论，控制在150字左右。"},
            {"role": "user", "content": f"请为下面的文章生成摘要：\n{article}。不要生成多余内容如字数统计等。"}
        ],
        temperature=0.2,  # 越低越稳定、越贴近原文
        max_tokens=300    # 摘要长度上限
    )
    # 输出结果
    summary = response.choices[0].message.content
    if summary:    
        db.update_news_summary(id, summary)
        print(f"文章 {id} 摘要：")
        print(summary)
        
