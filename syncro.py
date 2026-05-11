#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步脚本：将SQLite news表中最近一周的数据同步到PostgreSQL news_ts表
"""

import sqlite3
import psycopg2
from datetime import datetime, timedelta
import os

from logger import get_logger

logger = get_logger("syncro")

# PostgreSQL连接配置
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "vsb",
    "user": "vsb_read",
    "password": "rJqP2eySn@#T7An*@J"
}

# SQLite数据库路径
SQLITE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news.db")


def parse_datetime(dt_text):
    """将日期时间文本解析为datetime对象"""
    if not dt_text:
        return None
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_text, fmt)
        except ValueError:
            continue
    return None


def get_sqlite_recent_news(days=7):
    """从SQLite读取最近一周内的新闻数据"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "SELECT id, title, author, publish_time, source, content, summary, url, "
        "category, subcategory, final_category, created_at "
        "FROM news WHERE created_at >= ? "
        "AND (final_category IS NULL OR final_category NOT IN ('大模型排除', '待审')) "
        "ORDER BY created_at ASC",
        (cutoff_date,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def sync_to_pg(rows):
    """将数据同步到PostgreSQL"""
    if not rows:
        logger.info("没有需要同步的数据")
        return

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    synced_count = 0
    skipped_count = 0

    try:
        for row in rows:
            created_at = parse_datetime(row["created_at"])
            if created_at is None:
                logger.warning(f"跳过记录(created_at无法解析): {row['title']}")
                continue

            # 检查是否已存在（以created_at精确匹配）
            cur.execute(
                "SELECT 1 FROM news_ts WHERE created_at = %s",
                (created_at,)
            )
            if cur.fetchone():
                skipped_count += 1
                continue

            publish_time = parse_datetime(row["publish_time"])

            # 插入数据
            cur.execute(
                "INSERT INTO news_ts (id, title, author, publish_time, source, content, "
                "summary, url, category, subcategory, final_category, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    row["id"],
                    row["title"],
                    row["author"],
                    publish_time,
                    row["source"],
                    row["content"],
                    row["summary"],
                    row["url"],
                    row["category"],
                    row["subcategory"],
                    row["final_category"],
                    created_at,
                )
            )
            conn.commit()
            synced_count += 1
            logger.info(f"已同步: [{row['source']}] {row['title']} (created_at={row['created_at']})")

    except Exception as e:
        conn.rollback()
        logger.error(f"同步过程中发生错误: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    logger.info(f"同步完成: 新增 {synced_count} 条, 跳过 {skipped_count} 条(已存在)")


def main():
    logger.info("开始数据同步: SQLite -> PostgreSQL")
    logger.info(f"SQLite数据库: {SQLITE_DB}")
    logger.info(f"PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['dbname']}")

    # 读取最近一周的数据
    rows = get_sqlite_recent_news(days=7)
    logger.info(f"从SQLite读取到 {len(rows)} 条最近一周的记录")

    # 同步到PostgreSQL
    sync_to_pg(rows)

    logger.info("数据同步任务结束")


if __name__ == "__main__":
    main()
