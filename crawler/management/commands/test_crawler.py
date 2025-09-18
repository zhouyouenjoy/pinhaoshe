from django.core.management.base import BaseCommand
from crawler.models import CrawledUser, CrawledPost, CrawledMedia
from django.utils import timezone
import json


class Command(BaseCommand):
    help = '测试爬虫应用和数据库配置'

    def handle(self, *args, **options):
        # 测试创建一个爬虫用户
        user, created = CrawledUser.objects.using('crawler').get_or_create(
            username='test_user',
            platform='douyin',
            platform_user_id='123456',
            defaults={
                'nickname': '测试用户',
                'follower_count': 100,
                'following_count': 50,
                'post_count': 20
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'成功创建测试用户: {user.username}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'测试用户已存在: {user.username}')
            )
            
        # 测试创建一个内容
        post, created = CrawledPost.objects.using('crawler').get_or_create(
            title='测试内容',
            platform='douyin',
            platform_post_id='789012',
            user=user,
            posted_at=timezone.now(),
            defaults={
                'content': '这是一条测试内容',
                'like_count': 50,
                'comment_count': 10,
                'share_count': 5
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'成功创建测试内容: {post.title}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'测试内容已存在: {post.title}')
            )
            
        # 测试创建媒体文件
        media1, created1 = CrawledMedia.objects.using('crawler').get_or_create(
            media_type='image',
            url='https://example.com/test1.jpg',
            post=post,
            platform='douyin',
            defaults={
                'is_downloaded': False
            }
        )
        
        media2, created2 = CrawledMedia.objects.using('crawler').get_or_create(
            media_type='image',
            url='https://example.com/test2.jpg',
            post=post,
            platform='douyin',
            defaults={
                'is_downloaded': False
            }
        )
        
        if created1 or created2:
            self.stdout.write(
                self.style.SUCCESS(f'成功创建测试媒体文件')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'测试媒体文件已存在')
            )
            
        self.stdout.write(
            self.style.SUCCESS('爬虫应用测试完成!')
        )