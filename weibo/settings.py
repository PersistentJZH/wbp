# -*- coding: utf-8 -*-

import os

BOT_NAME = 'weibo'
SPIDER_MODULES = ['weibo.spiders']
NEWSPIDER_MODULE = 'weibo.spiders'
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_ENABLED = True
LOG_STDOUT = False
LOG_FILE = None

# 爬虫配置
CLOSESPIDER_TIMEOUT = 0  # 不设置超时
CLOSESPIDER_ITEMCOUNT = 0  # 不设置项目数量限制
CLOSESPIDER_PAGECOUNT = 0  # 不设置页面数量限制
CLOSESPIDER_ERRORCOUNT = 0  # 不设置错误数量限制

# 并发设置
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 1

# 下载设置
DOWNLOAD_TIMEOUT = 15
DOWNLOAD_MAXSIZE = 0
DOWNLOAD_WARNSIZE = 0
DOWNLOAD_DELAY = 1

# 允许下载图片的外部域名
SPIDER_ALLOWED_DOMAINS = ['image.baidu.com']

# 从环境变量获取cookie
WEIBO_COOKIE = os.getenv('WEIBO_COOKIE', '')

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'cookie': WEIBO_COOKIE,
}

# 自定义下载器中间件
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.offsite.OffsiteMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
}

# 启用缓存
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# 管道配置
ITEM_PIPELINES = {
    'weibo.pipelines.CsvPipeline': 300,
    'weibo.pipelines.DuplicatesPipeline': 400,
}

# 搜索配置
KEYWORD_LIST = ['包场', '观影']
WEIBO_TYPE = 3
CONTAIN_TYPE = 1
REGION = ['全部']
START_DATE = '2024-03-13'
END_DATE = '2024-03-13'
FURTHER_THRESHOLD = 10
LIMIT_RESULT = 10

# 文件存储路径
IMAGES_STORE = 'weibo_images'  # 图片存储目录
IMAGES_EXPIRES = 90  # 图片过期天数
IMAGES_MIN_HEIGHT = 100  # 最小图片高度
IMAGES_MIN_WIDTH = 100  # 最小图片宽度
FILES_STORE = './'

# 配置MongoDB数据库
# MONGO_URI = 'localhost'

# 配置MySQL数据库，以下为默认配置，可以根据实际情况更改，程序会自动生成一个名为weibo的数据库，如果想换其它名字请更改MYSQL_DATABASE值
# MYSQL_HOST = 'localhost'
# MYSQL_PORT = 3306
# MYSQL_USER = 'root'
# MYSQL_PASSWORD = '123456'
# MYSQL_DATABASE = 'weibo'

# 配置SQLite数据库
# SQLITE_DATABASE = 'weibo.db'

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 3  # 重试次数
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]  # 需要重试的HTTP状态码
