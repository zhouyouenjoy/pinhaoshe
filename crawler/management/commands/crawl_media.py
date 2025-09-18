import os
import sys
import django
from django.core.management.base import BaseCommand, CommandError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')
django.setup()

from crawler.spiders import DouyinSpider, XiaohongshuSpider, BilibiliSpider


class Command(BaseCommand):
    help = '从抖音、小红书、B站爬取照片数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--platform',
            type=str,
            help='指定平台: douyin, xiaohongshu, bilibili',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='用户主页URL',
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='无头模式运行',
        )

    def handle(self, *args, **options):
        platform = options['platform']
        url = options['url']
        headless = options['headless']

        if not platform or not url:
            self.stdout.write(
                self.style.ERROR('请提供平台名称和用户URL')
            )
            return

        if platform == 'douyin':
            spider = DouyinSpider(headless=headless)
        elif platform == 'xiaohongshu':
            spider = XiaohongshuSpider(headless=headless)
        elif platform == 'bilibili':
            spider = BilibiliSpider(headless=headless)
        else:
            self.stdout.write(
                self.style.ERROR(f'不支持的平台: {platform}')
            )
            return

        try:
            self.stdout.write(
                self.style.SUCCESS(f'开始爬取 {platform} 数据...')
            )
            spider.init_driver()
            # 这里添加实际的爬取逻辑
            spider.close_driver()
            self.stdout.write(
                self.style.SUCCESS('爬取完成')
            )
        except Exception as e:
            spider.close_driver()
            self.stdout.write(
                self.style.ERROR(f'爬取过程中出现错误: {str(e)}')
            )