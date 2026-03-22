import datetime
import json
from openai import OpenAI
import requests
from requests.compat import urlencode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from gne import GeneralNewsExtractor
import time
import re

import os
from dotenv import load_dotenv
from logger import info, debug, error, warning
from logger import info, debug, error, warning

class NewsExtractor:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.driver = self.init_driver()
        self.extractor = GeneralNewsExtractor()

        # 加载环境变量
        load_dotenv()

        # 获取API密钥
        self.api_key = os.getenv("WENXIN_API_KEY")
        self.secret_key = os.getenv("WENXIN_SECRET_KEY")
        self.ark_api_key = os.getenv("ARK_API_KEY")
        self.wexin_cookies = os.getenv("wechat_cookie").split("; ")
        for cookie in self.wexin_cookies:
            name, value = cookie.split("=",1)
            print(name + "=" + value)
        self.wexin_params = os.getenv("wechat_querystring").split("?")[1].split("&")
        pass

        
    
    def init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # 添加反检测措施
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # 获取Chrome驱动路径
        driver_path = ChromeDriverManager().install()
        
        try:
            # 尝试Selenium 4.x的方式
            from selenium.webdriver.chrome.service import Service
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except TypeError:
            # 如果失败，使用Selenium 3.x的方式
            driver = webdriver.Chrome(executable_path=driver_path, chrome_options=chrome_options)
        
        # 进一步反检测
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(10)
        return driver
    def get_article_links(self, fakeid="Mzg4MTAwMzgxNw==", begin=0,count=5,url="https://mp.weixin.qq.com/cgi-bin/appmsgpublish"):
        #url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"
        params = {}
        for param in self.wexin_params:
            name, value = param.split("=",1)
            params[name] = value

        params["fakeid"] = fakeid
        params["begin"] = begin
        params["count"] = count
        '''
        params = {
            "sub":"list",
            "search_field":"null",
            "begin": begin,
            "count": count,
            "query":"",
            "fakeid":fakeid,
            "type":"101_1",
            "free_publish_type":"1",
            "sub_action":"list_ex",
            "fingerprint":" ",
            "token":"747986180",
            "lang":"zh_CN",
            "f":"json",
            "ajax":"1"
        }
        '''
        # 将参数编码为查询字符串
        query_string = urlencode(params)

        # 拼接完整 URL
        full_url = f"{url}?{query_string}"
        # 或使用 urljoin（更安全，处理基础 URL 末尾是否有 / 的情况）
        # full_url = urljoin(base_url, f"?{query_string}")

        driver = webdriver.Chrome()


        driver.get(url)
        driver.implicitly_wait(2)
        
        '''
        # 设置cookie
        driver.add_cookie({"name": "appmsglist_action_3698171553", "value": "card"})
        driver.add_cookie({"name": "ua_id", "value": "gGciSNABsRG3YVjYAAAAAP3VzldzkVQpLuyW5trVEZU="})
        driver.add_cookie({"name": "wxuin", "value": "72840348896290"})
        driver.add_cookie({"name": "mm_lang", "value": "zh_CN"})
        driver.add_cookie({"name": "cert", "value": "etdJX8xT3oYOdzfDjW5AoMu3Nqu7zHaI"})
        driver.add_cookie({"name": "rand_info", "value": "CAESIHhReagY2zVfisxyfJ+5THLdltUd8GV+J8ttkaAzduRE"})
        driver.add_cookie({"name": "slave_bizuin", "value": "3698171553"})
        driver.add_cookie({"name": "data_bizuin", "value": "3698171553"})
        driver.add_cookie({"name": "bizuin", "value": "3698171553"})
        driver.add_cookie({"name": "data_ticket", "value": "BquUuCVDR438aB0N+ADA+GXzj+oKQM9ESmsdjolt2GvN8WGFJovX4BGLxvXyp1Wv"}) 
        driver.add_cookie({"name": "slave_user", "value": "gh_1b1c72a05bb7"})
        driver.add_cookie({"name": "xid", "value": "ce227841f747029bc23ebc19fa0ec802"}) 
        driver.add_cookie({"name": "_clsk", "value": "x90bsd|1773104838504|3|1|mp.weixin.qq.com/weheat-agent/payload/record"})
        driver.add_cookie({"name": "_clck", "value": "3698171553|1|g48|0"})

        #driver.add_cookie({"name": "pass_ticket", "value": "0_1f8c7e4d2c0e8e3f2b4a3e3c4a4d5b4"})
        #driver.add_cookie({"name": "rewardsn", "value": ""})
        driver.add_cookie({"name": "wxtokenkey", "value": "777"})
        #driver.add_cookie({"name": "wxuinkey", "value": "777"})

        driver.add_cookie({"name": "slave_sid", "value": "ZXk1UnRBTnRaeFYwMkN0RzZLOV9nXzhZM0FaWGxrWUpyNmVNd0N2X2sxME5wdEpWQUFJMmZmUHNnZGJnQXRLenZsblpFcGltN1FpV1lTaktNVWRHWlh1dkpTUVl5eWJ1TEQzNHBqYml6OEo1YzFORFdKUWYyYWd2YzVaSXBnRHBSWGd1VmxBaDJ5ZVpkOUhR"})
        '''
        for cookie in self.wexin_cookies:
            name, value = cookie.split("=",1)
            print('add cookie:'+ name+'='+value)
            driver.add_cookie({"name": name, "value": value})

        driver.get(full_url)

 
        # 等待页面加载完成
        driver.implicitly_wait(5)

        # 获取页面源码
        page_source = driver.page_source

        soup = BeautifulSoup(page_source, "html.parser")
                
        # pre标签
        moe_list_pre = soup.find("pre")
        if moe_list_pre:
                page_source = moe_list_pre.text
        
        data_json = json.loads(page_source)
        publish_list = json.loads(data_json["publish_page"])["publish_list"]
        links = []
        for publish_item in publish_list:
            publish_info=json.loads(publish_item["publish_info"])
            #print(publish_info)
            one_item = publish_info["appmsgex"][0]
            title,link, update_time = one_item["title"],one_item["link"],one_item["update_time"]
            #将日期由长整型转换为日期时间对象
            pub_time=datetime.datetime.fromtimestamp(int(update_time))
            links.append(link)

        return links

    def get_rendered_page(self, url):
        try:
            debug(f"正在获取页面: {url}")
            self.driver.get(url)
            
            # 针对今日头条增加更长的等待时间
            if "toutiao.com" in url:

                time.sleep(15)  # 更长的等待时间
                for i in range(1):
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(4)
            else:
                time.sleep(10)  # 普通网站的等待时间
            
            # 保存页面源代码以便调试
            if "toutiao.com" in url:
                with open("toutiao_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
            
            return self.driver.page_source
        except Exception as e:
            import traceback
            traceback.print_exc()
            error(f"获取渲染页面失败 {url}: {e}")
            error(traceback.format_exc())
            return None
    
    def extract_news_links(self, page_source, base_url):
        info(f"开始提取链接: {base_url}")
        
        links = []
        
        # 1. 针对教育部网站的特殊处理 - 只提取class="moe-list"的div下的链接
        if "moe.gov.cn" in base_url:
            info("教育部网站特殊处理", "extract")
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 查找class="moe-list"的div标签
            moe_list_div = soup.find("div", class_="moe-list")
            
            if moe_list_div:

                # 提取该div下所有a标签的href属性
                a_tags = moe_list_div.find_all("a", href=True)
        
                
                for a_tag in a_tags:
                    href = a_tag["href"]
                    if href and href not in ["#", "javascript:"]:
                        
                        # 构建完整URL - 在教育部网站条件块内部处理所有相对路径
                        if href.startswith("http"):
                            full_url = href
                        else:
                            # 确保base_url格式正确
                            if base_url.endswith("/index.html"):
                                base_url = base_url[:-11]
                            
                            # 确保base_url以/结尾
                            if not base_url.endswith("/"):
                                base_url += "/"
                            
                            # 处理各种相对路径
                            if href.startswith("/"):
                                # 根相对路径
                                full_url = base_url.split("://")[0] + "://" + base_url.split("://")[1].split("/")[0] + href
                            elif href.startswith("../"):
                                # 父目录相对路径
                                full_url = base_url + href
                            elif href.startswith("./"):
                                # 当前目录相对路径
                                full_url = base_url + href[2:]
                            else:
                                # 直接以文件名开头的相对路径
                                full_url = base_url + href
                        
                        links.append(full_url)
                
                if links:
                    # 去重
                    unique_links = list(set(links))
                    info(f"教育部网站提取到 {len(unique_links)} 条链接", "extract")
                    #return unique_links
                    return links
            else:
                warning("未找到class='moe-list'的div标签", "extract")
                return None
        
        # 2. 针对今日头条网站的特殊处理
        elif "toutiao.com" in base_url:
            info("今日头条网站特殊处理", "extract")

            soup = BeautifulSoup(page_source, "html.parser")
            
            # 1. 尝试查找class="main-l"的div标签
            main_l_div = soup.find("div", class_="main-l")
            
            if main_l_div:

                
                # 提取该div下所有a标签的href属性
                a_tags = main_l_div.find_all("a", href=True)
                
                for a_tag in a_tags:
                    href = a_tag["href"]
                    if href and href not in ["#", "javascript:"]:
                        
                        # 构建完整URL
                        if href.startswith("http"):
                            full_url = href
                        else:
                            # 确保base_url格式正确
                            if base_url.endswith("/index.html"):
                                base_url = base_url[:-11]
                            
                            # 确保base_url以/结尾
                            if not base_url.endswith("/"):
                                base_url += "/"
                            
                            # 处理各种相对路径
                            if href.startswith("/"):
                                # 根相对路径
                                full_url = base_url.split("://")[0] + "://" + base_url.split("://")[1].split("/")[0] + href
                            elif href.startswith("../"):
                                # 父目录相对路径
                                full_url = base_url + href
                            elif href.startswith("./"):
                                # 当前目录相对路径
                                full_url = base_url + href[2:]
                            else:
                                # 直接以文件名开头的相对路径
                                full_url = base_url + href
                        
                        links.append(full_url)
                
                if links:
                    # 去重
                    unique_links = list(set(links))
                    info(f"今日头条网站提取到 {len(unique_links)} 条链接", "extract")
                    return unique_links
            else:
                warning("未找到class='main-l'的div标签", "extract")
                return None

        
        # 3. 针对edu.cn网站的特殊处理 - 只提取class="section2ContentRightTitle"的div下的链接
        elif "edu.cn" in base_url:
            info("edu.cn网站特殊处理", "extract")

            soup = BeautifulSoup(page_source, "html.parser")
            
            # 查找所有class="section2ContentRightTitle"的div标签
            section_divs = soup.find_all("div", class_="section2ContentRightTitle")
            
            if section_divs:
                
                for section_div in section_divs:
                    # 提取该div下所有a标签的href属性
                    a_tags = section_div.find_all("a", href=True)                    
                    for a_tag in a_tags:
                        href = a_tag["href"]
                        if href and href not in ["#", "javascript:"]:
                            
                            # 构建完整URL
                            if href.startswith("http"):
                                full_url = href
                            else:
                                # 确保base_url格式正确
                                if base_url.endswith("/index.shtml"):
                                    base_url = base_url[:-12]
                                elif base_url.endswith("/index_1.shtml"): 
                                    base_url = base_url[:-15]
                                
                                # 确保base_url以/结尾
                                if not base_url.endswith("/"):
                                    base_url += "/"
                                
                                # 处理各种相对路径
                                if href.startswith("/"):
                                    # 根相对路径
                                    full_url = base_url.split("://")[0] + "://" + base_url.split("://")[1].split("/")[0] + href
                                elif href.startswith("../"):
                                    # 父目录相对路径
                                    full_url = base_url + href
                                elif href.startswith("./"):
                                    # 当前目录相对路径
                                    full_url = base_url + href[2:]
                                else:
                                    # 直接以文件名开头的相对路径
                                    full_url = base_url + href
                            
                            links.append(full_url)
                
                if links:
                    # 去重
                    unique_links = list(set(links))
                    info(f"edu.cn网站提取到 {len(unique_links)} 条链接", "extract")
                    return unique_links
            else:
                warning("未找到class='section2ContentRightTitle'的div标签", "extract")
                return None
        
        # 4. 针对ai-bot.cn网站的特殊处理 - 只提取class="news-item"的div下的前10条链接
        elif "ai-bot.cn" in base_url:
            info("ai-bot.cn网站特殊处理", "extract")
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 查找所有class="news-item"的div标签
            news_divs = soup.find_all("div", class_="news-item")
            
            if news_divs:
                
                # 只处理前10个news-item
                processed_count = 0
                max_items = 10
                
                for news_div in news_divs:
                    if processed_count >= max_items:
                        break
                    
                    # 提取该div下所有a标签的href属性
                    a_tags = news_div.find_all("a", href=True)
                    
                    for a_tag in a_tags:
                        href = a_tag["href"]
                        if href and href not in ["#", "javascript:"]:
                            
                            # 构建完整URL
                            if href.startswith("http"):
                                full_url = href
                            else:
                                # 确保base_url格式正确
                                if base_url.endswith("/index.html"):
                                    base_url = base_url[:-11]
                                
                                # 确保base_url以/结尾
                                if not base_url.endswith("/"):
                                    base_url += "/"
                                
                                # 处理各种相对路径
                                if href.startswith("/"):
                                    # 根相对路径
                                    full_url = base_url.split("://")[0] + "://" + base_url.split("://")[1].split("/")[0] + href
                                elif href.startswith("../"):
                                    # 父目录相对路径
                                    full_url = base_url + href
                                elif href.startswith("./"):
                                    # 当前目录相对路径
                                    full_url = base_url + href[2:]
                                else:
                                    # 直接以文件名开头的相对路径
                                    full_url = base_url + href
                            
                            links.append(full_url)
                    
                    processed_count += 1
                
                if links:
                    # 去重并只返回前10条
                    unique_links = list(set(links))[:10]
                    info(f"ai-bot.cn网站提取到 {len(unique_links)} 条链接", "extract")
                    return unique_links
            else:
                warning("未找到class='news-item'的div标签", "extract")
                return None
        
        # 5. 针对beijing.gov.cn网站的特殊处理 - 只提取class="listBox"的div下的链接
        elif "beijing.gov.cn" in base_url:
            info("beijing.gov.cn网站特殊处理", "extract")
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 查找class="listBox"的div标签
            listbox_ul = soup.find("ul", class_="list")
            
            if listbox_ul:
                
                # 提取该div下所有a标签的href属性
                a_tags = listbox_ul.find_all("a", href=True)

                for a_tag in a_tags:
                    href = a_tag["href"]
                    if href and href not in ["#", "javascript:"]:
                        
                        # 构建完整URL
                        if href.startswith("http"):
                            full_url = href
                        else:
                            # 确保base_url格式正确
                            if base_url.endswith("/index.html"):
                                base_url = base_url[:-11]
                            
                            # 确保base_url以/结尾
                            if not base_url.endswith("/"):
                                base_url += "/"
                            
                            # 处理各种相对路径
                            if href.startswith("/"):
                                # 根相对路径
                                full_url = base_url.split("://")[0] + "://" + base_url.split("://")[1].split("/")[0] + href
                            elif href.startswith("../"):
                                # 父目录相对路径
                                full_url = base_url + href
                            elif href.startswith("./"):
                                # 当前目录相对路径
                                full_url = base_url + href[2:]
                            else:
                                # 直接以文件名开头的相对路径
                                full_url = base_url + href
                        
                        links.append(full_url)
                
                if links:
                    # 去重
                    unique_links = list(set(links))
                    info(f"beijing.gov.cn网站提取到 {len(unique_links)} 条链接", "extract")
                    return unique_links
            else:
                warning("未找到class='listBox'的div标签", "extract")
                return None
        
        # 2. 通用链接提取逻辑（适用于其他网站或教育部网站未找到moe-list的情况）
        href_pattern = re.compile(r'href=["\'](.*?)["\']')
        all_hrefs = href_pattern.findall(page_source)
        debug(f"使用正则提取到 {len(all_hrefs)} 个href属性", "extract")

        
        for href in all_hrefs:
            if not href or href in ["#", "javascript:"]:
                continue
                
            # 构建完整URL
            if href.startswith("http"):
                full_url = href
            else:
                # 处理各种相对路径
                if base_url.endswith("/index.html"):
                    base_url = base_url[:-11]
                elif base_url.endswith("/index_1.htm"):
                    base_url = base_url[:-13]
                
                # 确保base_url以/结尾，便于拼接相对路径
                if not base_url.endswith("/"):
                    base_url += "/"
                
                # 处理相对路径
                if href.startswith("/"):
                    # 根相对路径
                    full_url = base_url.split("://")[0] + "://" + base_url.split("://")[1].split("/")[0] + href
                elif href.startswith("../"):
                    # 父目录相对路径
                    full_url = base_url + href
                elif href.startswith("./"):
                    # 当前目录相对路径
                    full_url = base_url + href[2:]
                else:
                    # 直接以文件名开头的相对路径
                    full_url = base_url + href
            
            links.append(full_url)
        
        # 3. 过滤重复链接
        unique_links = list(set(links))
        debug(f"去重后链接数量: {len(unique_links)}", "extract")
        
        # 4. 通用新闻链接过滤
        news_links = []
        for link in unique_links:
            link_lower = link.lower()
            
            # 排除明显不是新闻的链接
            if any(exclude in link_lower for exclude in ["javascript:", "mailto:", ".css", ".js", ".png", ".jpg", ".gif", ".pdf", ".doc", ".xls"]):
                continue
                
            # 包含新闻相关关键词的链接
            if any(keyword in link_lower for keyword in ["news", "article", "content", "info", "detail"]):
                news_links.append(link)
                debug(f"添加新闻链接: {link}", "extract")
            # 包含日期模式的链接
            elif re.search(r'\d{4}/\d{1,2}/\d{1,2}', link_lower):
                news_links.append(link)
                debug(f"添加日期链接: {link}", "extract")
            # 较长的链接（可能是新闻详情页）
            elif len(link) > 80 and ".html" in link_lower:
                news_links.append(link)
                debug(f"添加长链接: {link}", "extract")
        
        info(f"最终提取到 {len(news_links)} 条新闻链接", "extract")

        return news_links if news_links else unique_links[:20]  # 至少返回一些链接
    
    def extract_news_content(self, page_source, url):
        try:
            result = self.extractor.extract(page_source, noise_node_list=["//div[@class='comment']", "//div[@class='advertisement']"])
            
            # 确保所有必要字段都存在
            news_data = {
                "title": result.get("title", ""),
                "author": result.get("author", ""),
                "publish_time": result.get("publish_time", ""),
                "source": result.get("source", ""),
                "content": result.get("content", ""),
                "url": url
            }
            
            return news_data
        except Exception as e:
            error(f"提取新闻内容失败 {url}: {e}")
            return None
    
    def summarize_content(self, content):
        """生成新闻内容摘要，优先使用百度新闻摘要API，失败则使用备用方案"""
        if not content:
            return ""
        
        # 加载环境变量（把API Key存.env，不要硬编码）
        load_dotenv()
        api_key = os.getenv('ARK_API_KEY')

        # 初始化客户端（兼容OpenAI格式）
        client = OpenAI(
            api_key=api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        # 移除HTML标签
        soup = BeautifulSoup(content, "html.parser")
        article = soup.get_text()
        
        # 如果内容太短，直接返回
        if len(article) < 200:
            return article
        
        # 使用百度豆包摘要API
        response = client.chat.completions.create(
            model="doubao-seed-2-0-pro-260215",  # 模型ID，可在方舟控制台查看
            messages=[
                {"role": "system", "content": "你是一个专业的文本摘要助手，用简洁、通顺的中文生成文章摘要，保留核心信息和关键结论，控制在250字左右。"},
                {"role": "user", "content": f"请为下面的文章生成摘要：\n{article}。不要生成多余内容如字数统计等。"}
            ],
            temperature=0.2,  # 越低越稳定、越贴近原文
            max_tokens=400    # 摘要长度上限
        )
        # 输出结果
        summary = response.choices[0].message.content
        if summary:    

            print(f"生成摘要摘要：{summary}")
            return summary
        else:
            return ""

        

        
    
    def close(self):
        if self.driver:
            self.driver.quit()
    
    def classify_content(self, title, content):
        """使用百度智能云NLP分类API对内容进行分类"""
        if not title and not content:
            return "教育信息化", "其他"
        
        try:
            # 检查API密钥是否设置
            if not hasattr(self, 'api_key') or not self.api_key:
                raise ValueError("API密钥未设置")
            
            # 使用百度智能云NLP分类API
            API_KEY = self.api_key
            SECRET_KEY = self.secret_key
        
            # 获取 access token
            debug("正在获取access_token...", "classification")
            auth_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
            response = requests.get(auth_url, timeout=10)
            
            # 强制设置响应编码为UTF-8
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                raise Exception(f"获取access_token失败，状态码: {response.status_code}, 响应: {response.text}")
                
            # 手动解析JSON，确保编码正确
            import json
            auth_result = json.loads(response.text)
            if "error" in auth_result:
                raise Exception(f"获取access_token失败: {auth_result['error']}")
                
            access_token = auth_result.get("access_token")

            if not access_token:
                raise ValueError("获取access_token失败")
            
            info("获取access_token成功", "classification")

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
            
            # 准备请求参数，根据官方文档要求
            payload = {
                "title": title[:50],  # 标题限制500字
                "content": content[:500]  # 内容限制2000字
            }

            
            
            # 发送请求，使用json参数自动处理编码
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=15)
            
            
            # 根据检测到的编码解码
            try:
                response_text = response.content.decode('utf-8')
            except:
                # 如果解码失败，尝试使用utf-8
                response_text = response.content.decode('utf-8', errors='replace')
            
            if response.status_code != 200:
                raise Exception(f"API调用失败，状态码: {response.status_code}, 响应: {response_text}")
            
            # 手动解析JSON，确保编码正确
            result = json.loads(response_text)
            debug(f"百度智能云NLP分类API返回结果: {result}", "classification")

            
            if "error_code" in result:
                raise Exception(f"百度智能云NLP分类API返回错误: {result['error_msg']} (错误码: {result['error_code']})")
                
            # 解析分类结果
            main_category = "教育信息化"
            subcategories = []
            
            if "item" in result:
                item = result["item"]
                if "lv1_tag_list" in item:
                    # 一级分类
                    for tag in item["lv1_tag_list"]:
                        if "tag" in tag:
                            # 确保字符串编码正确
                            tag_name = tag["tag"]
                            if isinstance(tag_name, bytes):
                                tag_name = tag_name.decode('utf-8')
                            main_category = tag_name
                            break
                
                if "lv2_tag_list" in item:
                    # 二级分类
                    for tag in item["lv2_tag_list"]:
                        if "tag" in tag:
                            # 确保字符串编码正确
                            tag_name = tag["tag"]
                            if isinstance(tag_name, bytes):
                                tag_name = tag_name.decode('utf-8')
                            subcategories.append(tag_name)
                
                if "lv3_tag_list" in item:
                    # 三级分类
                    for tag in item["lv3_tag_list"]:
                        if "tag" in tag:
                            # 确保字符串编码正确
                            tag_name = tag["tag"]
                            if isinstance(tag_name, bytes):
                                tag_name = tag_name.decode('utf-8')
                            subcategories.append(tag_name)
            
            # 处理子分类
            subcategory_str = ", ".join(subcategories) if subcategories else ""
            
            # 确保最终结果是正确编码的字符串
            main_category = str(main_category)
            subcategory_str = str(subcategory_str)
            
            
            info(f"分类结果 - 主分类: {main_category}, 子分类: {subcategory_str}", "classification")
            return main_category, subcategory_str
            
        except Exception as e:
            error(f"百度智能云NLP分类API调用失败: {e}", "classification")
            # 回退到默认分类
            return "其他", "其他"