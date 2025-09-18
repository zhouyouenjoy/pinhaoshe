"""
爬虫数据库配置
"""

DATABASES = {
    'crawler': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'crawler_db.sqlite3',
    }
}

DATABASE_ROUTERS = ['crawler.router.CrawlerRouter']