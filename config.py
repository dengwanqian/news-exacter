# 信息来源URL列表
NEWS_SOURCES = [
    {
        "url":"http://www.moe.gov.cn/jyb_xwfb/gzdt_gzdt/index.html",  
        "source":"教育部官网-工作动态"
    },
    {
        "url":"http://www.moe.gov.cn/jyb_xwfb/s271/index.html",  
        "source":"教育部官网-政策解读"
    },
    {
        "url":"https://www.toutiao.com/c/user/token/CiiKeMCqF1WLUzJbc2sPgIUpWP07ThNbYWzsvUzlogkKr3Qyd79IQMY1GkkKPAAAAAAAAAAAAABQEt9BK3U1ycxEIwdxTR4LEcJSlW0QbN8jfMXnDg7O0EF07XaarJQkdm8bvWmTz2ehFxCp04kOGMPFg-oEIgEDng1CJQ==/?tab=article",
        "source":"今日头条高校之窗"
     },
    {
        "url":"https://www.edu.cn/xxh/tpxw/index.shtml",  
        "source":"中国教育和科研计算机网滚动新闻"
    },
        {
        "url":"https://www.edu.cn/xxh/tpxw/index_1.shtml",  
        "source":"中国教育和科研计算机网滚动新闻"
    },
    {
        "url":"http://www.chinaedunew.cn/xinwen.html",  
        "source":"中国教育新闻网新闻频道"
    },
    {
        "url":"http://www.chinaedunew.cn/jiaoyu.html", 
        "source":"中国教育新闻网教育频道"
    }
]

# 数据库配置
DB_PATH = "news.db"

# Selenium配置
SELENIUM_TIMEOUT = 30

# 提取配置
EXTRACT_TIMEOUT = 60

#筛选词
FILTER_KEYWORDS = ["信息化","AI", "数字化", "网络安全", "教学改革","智慧教室", "人工智能", "智能体","信息技术","教育技术"]