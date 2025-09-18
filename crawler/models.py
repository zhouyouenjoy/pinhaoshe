from django.db import models

# 平台选择
PLATFORM_CHOICES = [
    ('douyin', '抖音'),
    ('xiaohongshu', '小红书'),
    ('bilibili', 'B站'),
]

class CrawledUser(models.Model):
    """
    爬取的用户数据模型
    """
    # 用户基本信息
    username = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    
    # 平台相关信息
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_user_id = models.CharField(max_length=100)  # 平台用户ID
    
    # 用户统计信息
    follower_count = models.IntegerField(default=0)  # 粉丝数
    following_count = models.IntegerField(default=0)  # 关注数
    post_count = models.IntegerField(default=0)  # 发布内容数
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('platform', 'platform_user_id')
        verbose_name = '爬取用户'
        verbose_name_plural = '爬取用户'
    
    def __str__(self):
        return f"{self.platform} - {self.username}"


class CrawledPost(models.Model):
    """
    爬取的内容数据模型
    """
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    
    # 图片链接
    image_urls = models.JSONField(default=list)  # 存储图片URL列表
    
    # 关联信息
    user = models.ForeignKey(CrawledUser, on_delete=models.CASCADE, related_name='posts')
    
    # 平台相关信息
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_post_id = models.CharField(max_length=100)  # 平台内容ID
    
    # 时间信息
    posted_at = models.DateTimeField()  # 平台发布日期
    crawled_at = models.DateTimeField(auto_now_add=True)  # 爬取日期
    
    class Meta:
        unique_together = ('platform', 'platform_post_id')
        verbose_name = '爬取内容'
        verbose_name_plural = '爬取内容'
    
    def __str__(self):
        return f"{self.platform} - {self.title}"


class CrawledMedia(models.Model):
    """
    爬取的媒体文件数据模型
    """
    # 媒体类型
    MEDIA_TYPES = [
        ('image', '图片'),
        ('video', '视频'),
    ]
    
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    url = models.URLField()
    local_path = models.CharField(max_length=500, blank=True, null=True)
    
    # 关联内容
    post = models.ForeignKey(CrawledPost, on_delete=models.CASCADE, related_name='media_files')
    
    # 平台相关信息
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    downloaded_at = models.DateTimeField(auto_now_add=True)
    is_downloaded = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = '爬取媒体'
        verbose_name_plural = '爬取媒体'
    
    def __str__(self):
        return f"{self.platform} - {self.media_type} - {self.url}"