import sqlite3
from datetime import datetime

class NewsDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
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
            created_at TEXT NOT NULL
        )
        '''
        self.cursor.execute(sql)
        self.conn.commit()
    
    def insert_news(self, title, author, publish_time, source, content, summary, url):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = '''
            INSERT OR IGNORE INTO news (title, author, publish_time, source, content, summary, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.cursor.execute(sql, (title, author, publish_time, source, content, summary, url, now))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"插入新闻失败: {e}")
            return False
    
    def get_all_news(self, limit=None):
        sql = "SELECT * FROM news ORDER BY publish_time DESC"
        if limit:
            sql += f" LIMIT {limit}"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def close(self):
        if self.conn:
            self.conn.close()