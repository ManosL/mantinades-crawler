# Scrapy settings for mantinades_crawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os

BOT_NAME = 'mantinades_crawler'

SPIDER_MODULES = ['mantinades_crawler.spiders']
NEWSPIDER_MODULE = 'mantinades_crawler.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'mantinades_crawler (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False # NOTE: Purely for the purposes of this project

# TODO: CHANGE THE CODE IN ORDER TO ROTATE THEM IN ORDER TO BE UNDETECTED
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 18

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2

# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'mantinades_crawler.middlewares.MantinadesCrawlerSpiderMiddleware': 543,
#}

# Add Your ScrapeOps API key

SCRAPEOPS_API_KEY = os.environ['SCRAPEOPS_API_KEY']

# # Add In The ScrapeOps Extension
EXTENSIONS = {
   'scrapeops_scrapy.extension.ScrapeOpsMonitor': 500,
}


# Update The Download Middlewares
DOWNLOADER_MIDDLEWARES = {
   'scrapeops_scrapy.middleware.retry.RetryMiddleware': 550,
   'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
}

# LOG_ENABLED = True
# LOG_LEVEL = 'DEBUG'  # Or 'DEBUG' if you want very detailed logs
# LOG_FILE = '/spider.log'

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'mantinades_crawler.middlewares.MantinadesCrawlerDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'mantinades_crawler.pipelines.RemoveDuplicatesPipeline': 100,
   'mantinades_crawler.pipelines.MantinadesCrawlerPipeline': 300,
}

# Configuring the Feeds that we will save crawled data.
# The below snippet is only useful if you store the crawled data
# in a single file
# from mantinades_crawler.spiders.mantinades import DESTINATION_DIR

# FEEDS = {
#     f'{DESTINATION_DIR}/results.csv': {
#         'format': 'csv',
#         'encoding': 'utf8',
#         'store_empty': False,
#         'fields': ['id', 'topics', 'author', 'date', 'text'],
#     },
# }
#
# CSV_DELIMITER = '|'

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
