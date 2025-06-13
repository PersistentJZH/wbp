# -*- coding: utf-8 -*-

import os

# Scrapy settings for weibo project

BOT_NAME = 'weibo'

SPIDER_MODULES = ['weibo.spiders']
NEWSPIDER_MODULE = 'weibo.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 1

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
   'weibo.middlewares.WeiboDownloaderMiddleware': 543,
}

# Configure item pipelines
ITEM_PIPELINES = {
   'weibo.pipelines.WeiboPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'

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
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 1

# 下载设置
DOWNLOAD_TIMEOUT = 15
DOWNLOAD_MAXSIZE = 0
DOWNLOAD_WARNSIZE = 0

# 允许下载图片的外部域名
SPIDER_ALLOWED_DOMAINS = ['image.baidu.com']

# 从环境变量获取cookie
WEIBO_COOKIE = os.getenv('WEIBO_COOKIE', '')

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'User-Agent': USER_AGENT,
    'cookie': WEIBO_COOKIE,
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

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 3  # 重试次数
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]  # 需要重试的HTTP状态码
