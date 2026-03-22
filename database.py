import sqlite3
from datetime import datetime
from logger import info, debug, error, warning

class NewsDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()
    
    def connect(self):
        # 连接数据库时设置编码
        self.conn = sqlite3.connect(self.db_path)
        # 确保数据库连接使用UTF-8编码
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
    
    def create_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            author TEXT,
            publish_time TEXT,
            source TEXT,
            content TEXT,
            summary TEXT,
            url TEXT NOT NULL UNIQUE,
            category TEXT,
            subcategory TEXT,
            final_category TEXT,
            created_at TEXT NOT NULL
        )
        '''
        self.cursor.execute(sql)
        self.conn.commit()
    
    def insert_news(self, title, author, publish_time, source, content, summary, url, category=None, subcategory=None):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = '''
            INSERT OR IGNORE INTO news (title, author, publish_time, source, content, summary, url, category, subcategory, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.cursor.execute(sql, (title, author, publish_time, source, content, summary, url, category, subcategory, now))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"插入新闻失败: {e}", "database")
            return False
    
    def get_all_news(self, limit=None):

        sql = "SELECT * FROM news  where final_category != '待审' ORDER BY  publish_time DESC "
        if limit:
            sql += f" LIMIT {limit}"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def get_all_news_with_undecided(self, limit=None):

        sql = "SELECT * FROM news  ORDER BY  publish_time DESC "
        if limit:
            sql += f" LIMIT {limit}"
        self.cursor.execute(sql)
        return self.cursor.fetchall()   
    def is_title_exists(self, title):
        """检查标题是否已存在"""
        try:
            sql = "SELECT COUNT(*) FROM news WHERE title = ?"
            self.cursor.execute(sql, (title,))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            error(f"检查标题是否存在失败: {e}", "database")
            return False
    
    def update_news_summary(self, id, summary):
        try:
            sql = "UPDATE news SET summary = ? WHERE id = ?"
            self.cursor.execute(sql, (summary, id))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"更新新闻摘要失败: {e}", "database")
            return False
    
    
    def close(self):
        if self.conn:
            self.conn.close()