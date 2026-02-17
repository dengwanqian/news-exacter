import sqlite3

# 连接数据库
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

# 查看表结构
print("表结构:")
cursor.execute("PRAGMA table_info(news)")
columns = cursor.fetchall()
for col in columns:
    print(col)

# 查看新闻数量
print("\n新闻数量:")
cursor.execute("SELECT COUNT(*) FROM news")
count = cursor.fetchone()[0]
print(f"数据库中的新闻数量: {count}")

# 查看前几条新闻
if count > 0:
    print("\n前5条新闻:")
    cursor.execute("SELECT title, publish_time, url FROM news LIMIT 5")
    news = cursor.fetchall()
    for i, item in enumerate(news, 1):
        print(f"{i}. 标题: {item[0]}")
        print(f"   发布时间: {item[1]}")
        print(f"   URL: {item[2]}")
        print()

# 关闭数据库连接
conn.close()