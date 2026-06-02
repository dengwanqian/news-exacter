# 教育信息化新闻采集工具 - Windows 部署手册

## 一、环境要求

- **操作系统**: Windows 10 / Windows 11 / Windows Server 2019+
- **Python**: 3.9 ~ 3.12（推荐 3.11）
- **Chrome 浏览器**: 最新稳定版（用于 Selenium 渲染）
- **网络**: 可访问百度智能云、火山方舟 API（大模型服务）

---

## 二、GitHub 源码下载

### 方式 1：使用 Git 克隆

```bash
# 打开 CMD 或 PowerShell，进入目标目录
cd D:\\tools

# 克隆仓库
git clone https://github.com/<your-org>/news-exacter.git

# 进入项目目录
cd news-exacter
```

### 方式 2：直接下载 ZIP

1. 打开 GitHub 仓库页面
2. 点击 **Code** -> **Download ZIP**
3. 解压到本地目录，如 `D:\\tools\\news-exacter`

---

## 三、Python 环境准备

### 3.1 安装 Python

1. 访问 [Python 官网](https://www.python.org/downloads/) 下载 Windows 安装包
2. 安装时务必勾选 **"Add Python to PATH"**
3. 验证安装：

```bash
python --version
pip --version
```

### 3.2 创建虚拟环境（强烈推荐）

```bash
cd D:\\tools\\news-exacter

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\\Scripts\\activate

# 激活后命令行前缀会显示 (venv)
```

> 后续所有 `pip` 和 `python` 命令均需在虚拟环境激活状态下执行。

---

## 四、依赖包安装

项目依赖已整理在 `requirements.txt` 中，包含以下包：

| 包名 | 用途 |
|------|------|
| selenium | 浏览器自动化爬取 |
| requests | HTTP 请求（调用百度 NLP API） |
| beautifulsoup4 | HTML 解析 |
| lxml | HTML/XML 解析器 |
| webdriver-manager | ChromeDriver 管理（备用） |
| python-dotenv | 加载 `.env` 环境变量 |
| openai | 调用火山方舟大模型（兼容 OpenAI 格式） |
| jinja2 | HTML 模板渲染 |
| pdfkit | HTML 转 PDF |
| psycopg2-binary | PostgreSQL 数据库同步 |

### 安装命令

```bash
# 确保在虚拟环境中
venv\\Scripts\\activate

# 安装依赖
pip install -r requirements.txt
```

如遇网络问题，可使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 五、Selenium / ChromeDriver 环境准备

本项目使用 **Selenium + ChromeDriver** 进行网页动态渲染爬取。

### 5.1 安装 Chrome 浏览器

1. 下载并安装 [Google Chrome](https://www.google.cn/chrome/)
2. 查看 Chrome 版本：打开 Chrome -> 右上角菜单 -> 帮助 -> 关于 Google Chrome

### 5.2 准备 ChromeDriver

项目中已附带 `chromedriver.exe`，但需确保其版本与本地 Chrome 版本匹配。

#### 检查版本匹配

```bash
chromedriver.exe --version
```

#### 版本不匹配时更新

1. 访问 [ChromeDriver 下载页](https://chromedriver.chromium.org/downloads) 或 [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
2. 下载与本地 Chrome **主版本号一致** 的 `chromedriver-win64.zip`
3. 解压后将 `chromedriver.exe` 覆盖到项目根目录

#### 配置说明

代码中已硬编码使用项目目录下的 `chromedriver.exe`：

```python
driver_path = os.path.join(base_dir, "chromedriver.exe")
```

无需额外配置系统 PATH。

---

## 六、PDF 生成依赖环境准备

PDF 生成依赖 **wkhtmltopdf**，需单独安装系统级程序。

### 6.1 下载安装 wkhtmltopdf

1. 访问 [wkhtmltopdf 官网](https://wkhtmltopdf.org/downloads.html)
2. 下载 Windows 64-bit 安装包（如 `wkhtmltopdf-0.12.6-1.msvc2015-win64.exe`）
3. 双击安装，建议保持默认安装路径：`C:\\Program Files\\wkhtmltopdf\\`

### 6.2 验证安装

```bash
"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe" --version
```

### 6.3 路径配置

代码中已硬编码默认路径：

```python
config = pdfkit.configuration(wkhtmltopdf=r'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
```

若安装路径不同，请修改 `generate_html.py` 第 10 行。

---

## 七、环境变量配置（.env）

在项目根目录创建 `.env` 文件，用于存放敏感配置和 API 密钥。

> `.env` 文件已加入 `.gitignore`，不会被提交到 Git。

### 7.1 大模型调用环境变量

#### 火山方舟大模型（摘要生成 + 内容审核）

```env
ARK_API_KEY=your_ark_api_key_here
```

- **用途**：生成新闻摘要、审核内容是否属于教育信息化范畴
- **获取方式**：登录 [火山方舟控制台](https://console.volcengine.com/ark) -> 创建 API Key
- **模型**：代码中使用 `doubao-seed-2-0-pro-260215`，可在控制台确认可用性

#### 百度智能云 NLP（新闻分类）

```env
WENXIN_API_KEY=your_baidu_api_key_here
WENXIN_SECRET_KEY=your_baidu_secret_key_here
```

- **用途**：调用百度智能云话题分类 API，对新闻进行一级/二级/三级分类
- **获取方式**：
  1. 登录 [百度智能云](https://cloud.baidu.com/)
  2. 进入"自然语言处理"产品，创建应用
  3. 获取 API Key 和 Secret Key

### 7.2 数据爬取环境变量（微信公众号）

微信公众号文章列表的爬取需要登录后的 Cookie 和请求参数。

```env
wechat_cookie=your_wechat_cookie_string_here
wechat_querystring=https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&search_field=null&begin=0&count=5&query=&fakeid=xxx&type=101_1&free_publish_type=1&sub_action=list_ex&fingerprint=xxx&token=xxx&lang=zh_CN&f=json&ajax=1
```

#### Cookie 获取方法

1. 使用 Chrome 登录 [微信公众号平台](https://mp.weixin.qq.com/)
2. 按 `F12` 打开开发者工具 -> **Network** 标签
3. 进入"内容与互动" -> "草稿箱" 或 "发表记录"
4. 找到一个 `appmsgpublish` 请求
5. 右键该请求 -> **Copy** -> **Copy as cURL (bash)**
6. 从中提取：
   - `Cookie:` 后的完整字符串 -> 填入 `wechat_cookie`
   - 请求的完整 URL（含参数）-> 填入 `wechat_querystring`

> **注意**：Cookie 会过期，通常需要每隔几天重新更新一次。

### 7.3 完整 .env 模板

```env
# ==========================================
# 火山方舟大模型（摘要 + 审核）
# ==========================================
ARK_API_KEY=

# ==========================================
# 百度智能云 NLP（新闻分类）
# ==========================================
WENXIN_API_KEY=
WENXIN_SECRET_KEY=

# ==========================================
# 微信公众号爬取参数（需定期更新）
# ==========================================
wechat_cookie=
wechat_querystring=
```

---

## 八、数据库准备

### 8.1 SQLite（本地默认）

SQLite 为文件型数据库，无需额外安装。首次运行 `main.py` 时会自动在项目目录创建 `news.db`。

### 8.2 PostgreSQL（同步目标，可选）

如需将数据同步到 PostgreSQL，请确保：

1. 安装并启动 PostgreSQL 服务
2. 创建目标数据库和数据表
3. 修改 `syncro.py` 中的连接配置：

```python
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "vsb",
    "user": "vsb_read",
    "password": "your_password"
}
```

目标表结构参考：

```sql
CREATE TABLE news_ts (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT,
    publish_time TEXT,
    source TEXT,
    content TEXT,
    summary TEXT,
    url TEXT,
    category TEXT,
    subcategory TEXT,
    final_category TEXT,
    created_at TEXT
);
```

---

## 九、业务模块使用说明

### 9.1 数据爬取

**入口脚本**：`main.py`

**功能**：
- 遍历 `config.py` 中配置的多个新闻来源
- 使用 Selenium 渲染页面，提取新闻链接
- 访问每篇新闻详情页，提取标题、作者、发布时间、正文内容
- 调用火山方舟大模型生成摘要
- 调用百度 NLP API 进行初步分类
- 根据关键词、发布时间进行过滤
- 存入 SQLite 数据库

**运行命令**：

```bash
python main.py
```

**输出**：
- 控制台打印处理进度
- `news.db` 数据库文件
- `logs/` 目录下的运行日志
- `link_cache.json` 链接去重缓存

### 9.2 数据存储

**模块文件**：`database.py`

**数据表结构**（`news` 表）：

| 字段 | 说明 |
|------|------|
| id | 自增主键 |
| title | 新闻标题（唯一索引） |
| author | 作者 |
| publish_time | 发布时间 |
| source | 来源网站/公众号 |
| content | 正文内容（HTML） |
| summary | AI 生成摘要 |
| url | 原文链接（唯一索引） |
| category | 百度 NLP 一级分类 |
| subcategory | 百度 NLP 二级/三级分类 |
| final_category | 最终分类（含人工审核逻辑） |
| created_at | 入库时间 |

**检查数据库**：

```bash
python check_db.py
```

### 9.3 分类审改

**入口脚本**：`classify_existing_news.py`

**功能**：
- 对 `category` 为 NULL 的新闻调用百度 NLP 补充分类
- 对 `final_category` 为 NULL 的新闻进行最终分类判定
- 分类规则综合来源网站性质、标题关键词、百度分类结果
- 使用火山大模型审核非教育信息化内容，标记为 `9.大模型排除`
- 无法自动判定的重要新闻标记为 `待审`，需人工校核

**最终分类体系**：

| 分类 | 说明 |
|------|------|
| 1.行业新闻 | 教育信息化行业动态 |
| 2.专家视点 | 专家评论、观点文章 |
| 3.高校动态 | 各高校信息化相关新闻 |
| 4.科技前沿 | AI、科技前沿资讯 |
| 9.大模型排除 | 大模型判定为非教育信息化内容 |
| 待审 | 需人工审核确认 |

**运行方式**：

`main.py` 在爬取结束后会自动调用该模块。也可单独运行：

```bash
python classify_existing_news.py
```

### 9.4 HTML / PDF 生成

#### 生成已审核的周报（不含"待审"和"大模型排除"）

**脚本**：`generate_html.py`

**功能**：
- 读取近一周内 `final_category` 不为 `待审` / `大模型排除` 的新闻
- 按 `final_category` 排序
- 使用 Jinja2 渲染 `template.html` 模板
- 生成 HTML 文件 + PDF 文件

**运行命令**：

```bash
python generate_html.py
```

**输出示例**：
- `教育信息化一周资讯_20260511.html`
- `教育信息化一周资讯_20260511.pdf`

#### 生成含待审内容的周报

**脚本**：`generate_html_with_undecided.py`

**功能**：包含所有新闻（含待审），用于人工审核参考。

**运行命令**：

```bash
python generate_html_with_undecided.py
```

**输出示例**：
- `教育信息化一周资讯(含待审)_20260511_1547.html`

### 9.5 摘要重新生成

**脚本**：`summary_with_ark.py`

**功能**：对数据库中已有新闻重新调用火山方舟大模型生成摘要。

**运行命令**：

```bash
python summary_with_ark.py
```

### 9.6 数据同步（SQLite -> PostgreSQL）

**脚本**：`syncro.py`

**功能**：
- 读取 SQLite `news` 表中最近 7 天的数据
- 排除 `final_category` 为 `待审` / `大模型排除` 的记录
- 按 `created_at` 去重后同步到 PostgreSQL `news_ts` 表

**运行命令**：

```bash
python syncro.py
```

---

## 十、配置文件说明

**文件**：`config.py`

### 新闻来源配置

```python
NEWS_SOURCES = [
    {"url": "https://mp.weixin.qq.com/cgi-bin/appmsgpublish?fakeid=xxx", "source": "高校信息化名家汇"},
    {"url": "https://ai-bot.cn/daily-ai-news/", "source": "Ai机器人-每日AI新闻"},
    {"url": "http://www.moe.gov.cn/jyb_xwfb/gzdt_gzdt/index.html", "source": "教育部官网-工作动态"},
    # ... 更多来源
]
```

> 如需新增/修改爬取源，直接编辑此列表。注意：不同网站需要针对性的 HTML 解析逻辑，已在 `news_extractor.py` 中实现。

### 筛选关键词

```python
FILTER_KEYWORDS = ["信息化", "AI", "教育数字化", "网络安全", "智慧课堂", "智慧教室", "人工智能", "智能体", "信息技术", "教育技术", "赋能"]
```

> 新闻标题或正文必须包含以上至少一个关键词才会被保留。

### 其他配置

```python
DB_PATH = "news.db"              # SQLite 数据库路径
SELENIUM_TIMEOUT = 30            # 页面加载超时（秒）
EXTRACT_TIMEOUT = 60             # 内容提取超时（秒）
```

---

## 十一、日常运维 checklist

| 频率 | 操作 |
|------|------|
| 每周 | 运行 `python main.py` 执行数据爬取 + 分类 |
| 每周 | 运行 `python generate_html.py` 生成周报 |
| 每周 | 检查 HTML 中标记为 `待审` 的新闻，人工判定分类 |
| 按需 | 更新 `.env` 中的 `wechat_cookie` 和 `wechat_querystring` |
| 按需 | 运行 `python syncro.py` 同步数据到 PostgreSQL |
| 每月 | 清理 `logs/` 目录和过期的 `link_cache.json` |
| 每月 | 检查 Chrome 版本，更新 `chromedriver.exe` |

---

## 十二、常见问题排查

### Q1: 运行 main.py 时提示 "invalid session"

**原因**：微信公众号 Cookie 过期。

**解决**：重新登录公众号平台，按 7.2 节步骤更新 `.env` 中的 `wechat_cookie` 和 `wechat_querystring`。

### Q2: WebDriver 启动失败 / Session 失效

**原因**：Chrome 与 ChromeDriver 版本不匹配，或 Chrome 未安装。

**解决**：
1. 确认 Chrome 已安装
2. 下载与 Chrome 版本匹配的 ChromeDriver 覆盖到项目目录

### Q3: PDF 生成失败

**原因**：wkhtmltopdf 未安装或路径错误。

**解决**：
1. 确认 wkhtmltopdf 已安装（默认路径 `C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe`）
2. 如安装路径不同，修改 `generate_html.py` 第 10 行

### Q4: 百度 NLP 分类返回错误或乱码

**原因**：API 密钥错误、欠费、或网络问题。

**解决**：
1. 检查 `.env` 中的 `WENXIN_API_KEY` 和 `WENXIN_SECRET_KEY`
2. 登录百度智能云控制台查看 API 调用量和余额
3. 查看 `logs/` 目录中的详细错误日志

### Q5: 火山方舟大模型调用失败

**原因**：API Key 错误、模型 ID 失效、或网络问题。

**解决**：
1. 检查 `.env` 中的 `ARK_API_KEY`
2. 登录火山方舟控制台确认模型 `doubao-seed-2-0-pro-260215` 可用
3. 如模型 ID 变更，修改 `news_extractor.py` 和 `classify_existing_news.py` 中的模型名称

### Q6: PostgreSQL 同步失败

**原因**：连接配置错误或网络不通。

**解决**：
1. 检查 `syncro.py` 中的 `PG_CONFIG`
2. 确认 PostgreSQL 服务已启动且可连接
3. 确认目标表 `news_ts` 已创建

---

## 十三、目录结构一览

```
news-exacter/
├── .env                          # 环境变量（敏感配置，需手动创建）
├── .gitignore
├── chromedriver.exe              # Chrome 驱动
├── config.py                     # 新闻源、关键词等配置
├── database.py                   # SQLite 数据库操作
├── logger.py                     # 日志模块
├── main.py                       # 主爬虫入口
├── news_extractor.py             # 新闻提取器（Selenium + GNE）
├── classify_existing_news.py     # 新闻分类与审核
├── generate_html.py              # 生成 HTML + PDF（已审内容）
├── generate_html_with_undecided.py  # 生成 HTML（含待审）
├── summary_with_ark.py           # 摘要重新生成
├── syncro.py                     # SQLite -> PostgreSQL 同步
├── check_db.py                   # 数据库检查工具
├── template.html                 # HTML 模板
├── requirements.txt              # Python 依赖
├── news.db                       # SQLite 数据库（首次运行后生成）
├── link_cache.json               # 链接去重缓存
├── logs/                         # 日志目录
└── gne_local/                    # 本地修改的 GeneralNewsExtractor
    ├── __init__.py
    ├── defaults.py
    ├── utils.py
    └── extractor/
        ├── __init__.py
        ├── AuthorExtractor.py
        ├── ContentExtractor.py
        ├── SourceExtractor.py
        ├── TimeExtractor.py
        └── TitleExtractor.py
```

---

## 十四、联系与支持

如遇部署问题，请检查 `logs/` 目录下的日志文件获取详细错误信息，并根据 常见问题排查 章节进行排查。
