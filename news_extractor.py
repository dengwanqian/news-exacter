import json
import requests
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
    
    def get_rendered_page(self, url):
        try:
            print(f"正在获取页面: {url}")
            self.driver.get(url)
            
            # 针对今日头条增加更长的等待时间
            if "toutiao.com" in url:
                print("检测到今日头条，增加等待时间...")
                time.sleep(15)  # 更长的等待时间
                
                # 尝试滚动页面以加载更多内容
                print("尝试滚动页面...")
                for i in range(2):
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(4)
            else:
                time.sleep(10)  # 普通网站的等待时间
            
            # 保存页面源代码以便调试
            if "toutiao.com" in url:
                with open("toutiao_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print("今日头条页面已保存到 toutiao_page.html")
            
            return self.driver.page_source
        except Exception as e:
            print(f"获取渲染页面失败 {url}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_news_links(self, page_source, base_url):
        print(f"\n开始提取链接: {base_url}")
        
        links = []
        
        # 1. 针对教育部网站的特殊处理 - 只提取class="moe-list"的div下的链接
        if "moe.gov.cn" in base_url:
            print("\n--- 教育部网站特殊处理 ---")
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 查找class="moe-list"的div标签
            moe_list_div = soup.find("div", class_="moe-list")
            
            if moe_list_div:
                print("找到class='moe-list'的div标签")
                
                # 提取该div下所有a标签的href属性
                a_tags = moe_list_div.find_all("a", href=True)
                print(f"在moe-list div下找到 {len(a_tags)} 个a标签")
                
                for a_tag in a_tags:
                    href = a_tag["href"]
                    if href and href not in ["#", "javascript:"]:
                        print(f"找到链接: {href}")
                        
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
                    print(f"\n教育部网站提取到 {len(unique_links)} 条链接")
                    #return unique_links
                    return links
            else:
                print("未找到class='moe-list'的div标签")
                return None
        
        # 2. 针对今日头条网站的特殊处理
        elif "toutiao.com" in base_url:
            print("\n--- 今日头条网站特殊处理 ---")
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 1. 尝试查找class="main-l"的div标签
            main_l_div = soup.find("div", class_="main-l")
            
            if main_l_div:
                print("找到class='main-l'的div标签")
                
                # 提取该div下所有a标签的href属性
                a_tags = main_l_div.find_all("a", href=True)
                print(f"在main-l div下找到 {len(a_tags)} 个a标签")
                
                for a_tag in a_tags:
                    href = a_tag["href"]
                    if href and href not in ["#", "javascript:"]:
                        print(f"找到链接: {href}")
                        
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
                    print(f"\n今日头条网站提取到 {len(unique_links)} 条链接")
                    return unique_links
            else:
                print("未找到class='main-l'的div标签")
                
                # 2. 备选方案：查找所有可能的文章链接
                print("尝试备选方案：查找所有可能的文章链接")
                all_a_tags = soup.find_all("a", href=True)
                print(f"找到 {len(all_a_tags)} 个a标签")
                
                for a_tag in all_a_tags:
                    href = a_tag["href"]
                    if href and href not in ["#", "javascript:"]:
                        # 筛选可能的文章链接
                        if "article" in href or "item" in href or len(href) > 50:
                            print(f"找到可能的文章链接: {href}")
                            
                            # 构建完整URL
                            if href.startswith("http"):
                                full_url = href
                            elif href.startswith("/"):
                                full_url = "https://www.toutiao.com" + href
                            else:
                                continue
                            
                            links.append(full_url)
                
                if links:
                    # 去重
                    unique_links = list(set(links))
                    print(f"\n备选方案提取到 {len(unique_links)} 条链接")
                    return unique_links
                else:
                    print("无法从今日头条提取链接，考虑使用API方案")
                    return None
        
        # 3. 针对edu.cn网站的特殊处理 - 只提取class="section2ContentRightTitle"的div下的链接
        elif "edu.cn" in base_url:
            print("\n--- edu.cn网站特殊处理 ---")
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 查找所有class="section2ContentRightTitle"的div标签
            section_divs = soup.find_all("div", class_="section2ContentRightTitle")
            
            if section_divs:
                print(f"找到 {len(section_divs)} 个class='section2ContentRightTitle'的div标签")
                
                for section_div in section_divs:
                    # 提取该div下所有a标签的href属性
                    a_tags = section_div.find_all("a", href=True)
                    print(f"在section2ContentRightTitle div下找到 {len(a_tags)} 个a标签")
                    
                    for a_tag in a_tags:
                        href = a_tag["href"]
                        if href and href not in ["#", "javascript:"]:
                            print(f"找到链接: {href}")
                            
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
                    print(f"\nedu.cn网站提取到 {len(unique_links)} 条链接")
                    return unique_links
            else:
                print("未找到class='section2ContentRightTitle'的div标签")
                return None
        
        # 4. 针对ai-bot.cn网站的特殊处理 - 只提取class="news-item"的div下的前10条链接
        elif "ai-bot.cn" in base_url:
            print("\n--- ai-bot.cn网站特殊处理 ---")
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 查找所有class="news-item"的div标签
            news_divs = soup.find_all("div", class_="news-item")
            
            if news_divs:
                print(f"找到 {len(news_divs)} 个class='news-item'的div标签")
                
                # 只处理前10个news-item
                processed_count = 0
                max_items = 10
                
                for news_div in news_divs:
                    if processed_count >= max_items:
                        break
                    
                    # 提取该div下所有a标签的href属性
                    a_tags = news_div.find_all("a", href=True)
                    print(f"在news-item div下找到 {len(a_tags)} 个a标签")
                    
                    for a_tag in a_tags:
                        href = a_tag["href"]
                        if href and href not in ["#", "javascript:"]:
                            print(f"找到链接: {href}")
                            
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
                    print(f"\nai-bot.cn网站提取到 {len(unique_links)} 条链接")
                    return unique_links
            else:
                print("未找到class='news-item'的div标签")
                return None
        
        # 2. 通用链接提取逻辑（适用于其他网站或教育部网站未找到moe-list的情况）
        href_pattern = re.compile(r'href=["\'](.*?)["\']')
        all_hrefs = href_pattern.findall(page_source)
        print(f"使用正则提取到 {len(all_hrefs)} 个href属性")
        
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
        print(f"去重后链接数量: {len(unique_links)}")
        
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
                print(f"添加新闻链接: {link}")
            # 包含日期模式的链接
            elif re.search(r'\d{4}/\d{1,2}/\d{1,2}', link_lower):
                news_links.append(link)
                print(f"添加日期链接: {link}")
            # 较长的链接（可能是新闻详情页）
            elif len(link) > 80 and ".html" in link_lower:
                news_links.append(link)
                print(f"添加长链接: {link}")
        
        print(f"\n最终提取到 {len(news_links)} 条新闻链接")
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
            print(f"提取新闻内容失败 {url}: {e}")
            return None
    
    def summarize_content(self, content):
        """生成新闻内容摘要，优先使用百度新闻摘要API，失败则使用备用方案"""
        if not content:
            return ""
        
        # 移除HTML标签
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()
        
        # 如果内容太短，直接返回
        if len(text) < 100:
            return text
        
        # 打印原始内容前100字，便于调试
        print(f"\n原始内容前100字: {text[:100]}...")
        print(f"原始内容长度: {len(text)}字")
        
        try:
            # 检查API密钥是否设置
            if not hasattr(self, 'api_key') or not self.api_key:
                raise ValueError("API密钥未设置")
            
            # 使用百度新闻摘要API
            API_KEY = self.api_key
            SECRET_KEY = self.secret_key
        
            # 获取 access token
            print("正在获取access_token...")
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
            
            print("获取access_token成功")

            # 调用百度新闻摘要API
            print("正在调用百度新闻摘要API...")
            url = "https://aip.baidubce.com/rpc/2.0/nlp/v1/news_summary"
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json; charset=utf-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            params = {"access_token": access_token}
            
            # 准备请求参数
            payload = {
                "content": text[:2000],  # 限制内容长度为2000字
                "max_summary_len": 300  # 摘要最大长度
            }
            
            # 手动序列化JSON，确保编码正确
            json_payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            
            # 发送请求
            response = requests.post(url, headers=headers, params=params, data=json_payload, timeout=15)
            
            # 强制设置响应编码为UTF-8
            response.encoding = 'utf-8'
            
            print(f"API响应状态码: {response.status_code}")
            print(f"响应编码: {response.encoding}")
            print(f"响应内容: {response.text}")
            
            if response.status_code != 200:
                raise Exception(f"API调用失败，状态码: {response.status_code}, 响应: {response.text}")
            
            # 手动解析JSON，确保编码正确
            result = json.loads(response.text)
            print(f"API返回结果: {result}")
            
            if "error_code" in result:
                raise Exception(f"API返回错误: {result['error_msg']} (错误码: {result['error_code']})")
                
            if "summary" in result:
                summary = result["summary"]
                # 确保摘要编码正确
                if isinstance(summary, bytes):
                    summary = summary.decode('utf-8')
                print(f"生成的摘要: {summary}")
                print(f"摘要长度: {len(summary)}字")
                return summary
            else:
                raise Exception(f"API返回结果中没有summary字段: {result}")
                
        except Exception as e:
            print(f"百度新闻摘要API调用失败: {e}")
            # 回退到简单摘要
            print("使用备用方案生成摘要...")
            # 尝试使用简单的摘要生成方法
            sentences = text.split('。')
            if len(sentences) > 3:
                # 取前三个句子作为摘要
                summary = '。'.join(sentences[:3]) + '。'
                print(f"备用方案生成的摘要: {summary}")
                return summary
            else:
                # 取前200字作为摘要
                summary = text[:200] + "..." if len(text) > 200 else text
                print(f"备用方案生成的摘要: {summary}")
                return summary
        
    
    def close(self):
        if self.driver:
            self.driver.quit()