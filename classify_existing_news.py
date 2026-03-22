#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对数据库中category字段为NULL的新闻条目进行分类
"""

import sqlite3
import requests
import json
from datetime import datetime
from logger import info, debug, error, warning


class NewsDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        # 连接数据库时设置编码
        self.conn = sqlite3.connect(self.db_path)
        # 确保数据库连接使用UTF-8编码
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
    
    def get_news_without_category(self):
        """获取category为NULL的新闻"""
        sql = "SELECT id, title, summary as content FROM news WHERE category IS NULL"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def get_news_without_final_category(self):
        """获取final_category为NULL的新闻"""
        sql = "SELECT id, title, summary as content, category, subcategory,source,author FROM news WHERE final_category IS NULL"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def update_category(self, news_id, category, subcategory):
        """更新新闻的分类信息"""
        try:
            sql = "UPDATE news SET category = ?, subcategory = ? WHERE id = ?"
            self.cursor.execute(sql, (category, subcategory, news_id))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"更新分类失败: {e}", "database")
            return False
    def update_final_category(self, news_id, final_category):
        """更新新闻的最终分类信息"""
        try:
            sql = "UPDATE news SET final_category = ? WHERE id = ?"
            self.cursor.execute(sql, (final_category, news_id))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"更新最终分类失败: {e}", "database")
            return False
    
    def close(self):
        if self.conn:
            self.conn.close()

class CategoryClassifier:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
    
    def get_access_token(self):
        """获取百度智能云API的access token"""
        try:
            auth_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
            response = requests.get(auth_url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                raise Exception(f"获取access_token失败，状态码: {response.status_code}")
                
            auth_result = response.json()
            if "error" in auth_result:
                raise Exception(f"获取access_token失败: {auth_result['error']}")
                
            access_token = auth_result.get("access_token")
            if not access_token:
                raise ValueError("获取access_token失败")
                
            return access_token
        except Exception as e:
            error(f"获取access_token失败: {e}", "classification")
            return None
    
    def classify(self, title, content):
        """使用百度智能云NLP分类API对内容进行分类"""
        if not title and not content:
            return "其他", "其他"
        
        try:
            # 获取access token
            access_token = self.get_access_token()
            if not access_token:
                raise ValueError("获取access_token失败")
            
            # 调用百度智能云NLP分类API - 文本分类
            debug("正在调用百度智能云NLP分类API...", "classification")
            url = "https://aip.baidubce.com/rpc/2.0/nlp/v1/topic"
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json; charset=utf-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            #params = {"access_token": access_token}
            params = {"access_token": access_token,
                      "charset": "UTF-8"}
            
            # 准备请求参数
            payload = {
                "title": title[:40],
                "content": content[:1500]
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=15)
            

            
            # 解析结果
            result = json.loads(response.content)
            
            if "error_code" in result:
                raise Exception(f"API返回错误: {result['error_msg']} (错误码: {result['error_code']})")
            
            # 提取分类信息
            main_category = "教育信息化"
            subcategories = []
            
            if "item" in result:
                item = result["item"]
                if "lv1_tag_list" in item:
                    for tag in item["lv1_tag_list"]:
                        if "tag" in tag:
                            main_category = str(tag["tag"])
                            break
                
                if "lv2_tag_list" in item:
                    for tag in item["lv2_tag_list"]:
                        if "tag" in tag:
                            subcategories.append(str(tag["tag"]))
                
                if "lv3_tag_list" in item:
                    for tag in item["lv3_tag_list"]:
                        if "tag" in tag:
                            subcategories.append(str(tag["tag"]))
            
            # 处理子分类
            subcategory_str = ", ".join(subcategories) if subcategories else ""
            
            # 确保编码正确
            main_category = str(main_category)
            subcategory_str = str(subcategory_str)
            
            return main_category, subcategory_str
            
        except Exception as e:
            error(f"分类失败: {e}", "classification")
            return "其他", "其他"
    def final_classify(self, title, content, category, subcategory, source, author):
        """根据标题、内容、分类、子分类、来源和作者进行最终分类"""
        # 这里可以添加复杂的分类逻辑
        # 例如，根据标题、内容、分类、子分类、来源和作者进行判断
        # 返回最终的分类结果
        final_category = "待审"
        if source == "Ai机器人-每日AI新闻" :
            final_category = "4.科技前沿"
            if category != "科技":
                final_category = "待审"
        elif source == "中国教育和科研计算机网滚动新闻":
            final_category = "1.行业新闻"
            #如果category等于教育且subcategory包含大学
            if any(keyword in content for keyword in ["本文","主任谈","观点","专家","哪些","学术","讲座"]):
                final_category = "2.专家视点"
            elif  category == "教育" and subcategory.find("大学") != -1:
                final_category = "3.高校动态"
        elif source.startswith("中国教育新闻网"):
            final_category = "1.行业新闻"
            if author == "胡编":
                final_category = "待审"
            elif  not category in ["教育","科技","时事"]:
                final_category = "待审"
            elif  category == "教育" and subcategory.find("大学") != -1:
                final_category = "3.高校动态"
        elif source == "今日头条高校之窗":
            final_category = "3.高校动态"
            if not category in ["教育","科技","时事"]:
                final_category = "待审"
        elif source == "教育部官网-政策解读":
            final_category = "2.专家视点"
        elif source == "教育部官网-工作动态":
            final_category = "1.行业新闻"
            if not category in ["教育","科技"]:
                final_category = "待审"
        elif source == "北京市政府官网-北京要闻":
            final_category = "1.行业新闻"
            if not category in ["教育","科技"]:
                final_category = "待审"
        elif source== "高校信息化名家汇":
                final_category = "3.高校动态"
        elif source == "教育信息化100人" :
                final_category = "2.专家视点"
        elif source == "教育信息化资讯":
                final_category = "1.行业新闻"
                if any(keyword in title for keyword in ["时评","聚焦","建议","主任谈","专家","文章"]):
                    final_category = "2.专家视点"
        elif source == "中国教育协会":
                final_category = "1.行业新闻"
                if any(keyword in title for keyword in ["时评","聚焦","建议","主任谈","专家","文章"]):
                    final_category = "2.专家视点"

        elif source == "中国高等教育协会":
                final_category = "1.行业新闻"
                if any(keyword in title for keyword in ["时评","聚焦","建议","主任谈","专家"]):
                    final_category = "2.专家视点"
                elif  category == "教育" and subcategory.find("大学") != -1:
                    final_category = "3.高校动态"
                elif category == "科技" :
                    final_category = "4.科技前沿"
        elif source == "中国教育技术协会":
                final_category = "1.行业新闻"
                if any(keyword in title for keyword in ["聚焦","建议","主任谈","专家"]):
                    final_category = "2.专家视点"
                elif  category == "科技" or subcategory.find("科技") != -1:
                    final_category = "4.科技前沿"
        return final_category

def main():
    # 从环境变量文件中获取API密钥
    from dotenv import load_dotenv
    import os
    
    # 加载环境变量
    load_dotenv()
    

    API_KEY = os.getenv("WENXIN_API_KEY")
    SECRET_KEY = os.getenv("WENXIN_SECRET_KEY")
    
    # 检查API密钥是否设置
    if not API_KEY or not SECRET_KEY:
        error("错误：API密钥未设置，请在.env文件中设置BAIDU_API_KEY和BAIDU_SECRET_KEY")
        return
    
    # 连接数据库
    db = NewsDatabase("news.db")
    
    # 初始化分类器
    classifier = CategoryClassifier(API_KEY, SECRET_KEY)
    
    # 获取需要分类的新闻
    news_list = db.get_news_without_category()
    info(f"找到 {len(news_list)} 条需要分类的新闻", "classification")

    
    # 处理每条新闻
    for news in news_list:
        news_id, title, summary, source, author = news
        debug(f"处理新闻 ID: {news_id}, 标题: {title[:50]}...", "classification")
        
        # 分类
        category, subcategory = classifier.classify(title, summary)
        info(f"分类结果: 分类={category}, 子分类={subcategory}", "classification")
        
        # 更新数据库
        success = db.update_category(news_id, category, subcategory)
        if success:
            #info(f"更新分类成功:"+title, "database")
            pass
        else:
            error(f"更新分类失败:{title}", "database")
    

    news_list = db.get_news_without_final_category()
   # 处理每条新闻
    for news in news_list:
        news_id, title, summary, category, subcategory,source, author = news
        final_category = classifier.final_classify(title, summary, category, subcategory, source, author)
        
        # 更新数据库
        success = db.update_final_category(news_id, final_category)
        if success:
            info(f"更新分类成功:{title}:{final_category}", "database")
        else:
            error(f"更新分类失败:{title}:{final_category}", "database")


    # 关闭数据库连接
    db.close()
    info("分类完成", "classification")

if __name__ == "__main__":
    main()