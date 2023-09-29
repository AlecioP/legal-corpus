# Scrapy settings for automotive project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "automotive"

SPIDER_MODULES = ["automotive.spiders"]
NEWSPIDER_MODULE = "automotive.spiders"



ROBOTSTXT_OBEY = False

#USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"


REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Custom

LOG_LEVEL = "INFO"
LOG_FILE = "automotive.log"
LOG_FILE_APPEND = False

RETRY_ENABLED =  False
CONCURRENT_REQUESTS = 100

# SPLASH

SPLASH_URL = 'http://192.168.1.3:8050/'

