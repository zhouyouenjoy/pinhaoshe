from django.db import models
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import os

# 平台选择
PLATFORM_CHOICES = [
    ('douyin', '抖音'),
    ('xiaohongshu', '小红书'),
    ('bilibili', 'B站'),
]

class CrawlerUser(models.Model):
    """
    与Django自带User表结构相同的用户表
    """
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # 添加密码字段
    password = models.CharField(max_length=128, default='pbkdf2_sha256$260000$AIgaFC17pg0j3dM65xrI0w$gcbS6m0S0I2F8wQ8S14GFgEz2nIQTM0gD5nVjE5V9uM=')
    
    # 头像URL（存储网络图片URL）
    avatar_url = models.URLField(blank=True, null=True)
    
    # 本地头像文件路径
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = '爬虫用户'
        verbose_name_plural = '爬虫用户'


class CrawledPost(models.Model):
    """
    爬取的内容数据模型
    """
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    
    # 图片链接
    image_urls = models.JSONField(default=list)  # 存储图片URL列表
    
    # 关联信息
    user = models.ForeignKey(CrawlerUser, on_delete=models.CASCADE, related_name='posts')
    
    # 平台相关信息
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_post_id = models.CharField(max_length=100)  # 平台内容ID
    
    # 统计信息
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    
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

class Photo(models.Model):
    title = models.CharField(max_length=200)
    
    image = models.ImageField(upload_to='photos/', blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)  # 添加外部链接字段
    
    uploaded_by = models.ForeignKey(CrawlerUser, on_delete=models.CASCADE, related_name='crawler_photos', null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    approved = models.BooleanField(default=False)
    
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null=True, blank=True, related_name='photos')
    
    def __str__(self):
        return self.title
    
    @property
    def image_url(self):
        """
        返回图片的URL，优先返回外部链接，如果没有则返回本地图片URL
        """
        if self.external_url:
            return self.external_url
        elif self.image:
            return self.image.url
        return None
    
    def save(self, *args, **kwargs):
        # 如果有外部链接，就不处理本地图片
        if self.external_url:
            super().save(*args, **kwargs)
            return
            
        # 先保存原始图片以获取文件大小
        super().save(*args, **kwargs)
        
        # 获取图片文件大小（字节）
        if hasattr(self.image, 'size'):
            file_size = self.image.size
        else:
            file_size = os.path.getsize(self.image.path)
        
        # 对于小于1MB的图片，保持原始质量
        if file_size < 1048576:  # 1MB = 1024 * 1024 bytes
            # 只进行必要的格式转换（如果需要），不压缩主图
            img = Image.open(self.image)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                # 转换为RGB模式
                img = img.convert('RGB')
                # 保存为JPEG格式，质量为最高
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=100, optimize=False)
                buffer.seek(0)
                self.image = InMemoryUploadedFile(
                    buffer, 'ImageField', os.path.basename(self.image.name),
                    'image/jpeg', buffer.tell(), None
                )
                # 重新保存
                super().save(*args, **kwargs)
            # 如果不需要转换模式，则保持原图不变
        else:
            # 对于大于1MB的图片，进行适度压缩
            img = Image.open(self.image.path)
            
            # 提高图片尺寸限制以保持更高清晰度
            if img.height > 1200 or img.width > 1200:
                output_size = (1200, 1200)
                img.thumbnail(output_size, Image.Resampling.LANCZOS)
                img.save(self.image.path, quality=90, optimize=True)
            
            # 处理主图片 - 提高清晰度
            if self.image and hasattr(self.image, 'name'):
                img = Image.open(self.image)
                # Convert RGBA to RGB for JPEG compatibility
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGB')
                
                # 提高最大尺寸以保持清晰度
                max_size = (1200, 1200)
                if img.height > max_size[0] or img.width > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=90, optimize=True)
                buffer.seek(0)
                self.image = InMemoryUploadedFile(
                    buffer, 'ImageField', os.path.basename(self.image.name),
                    'image/jpeg', buffer.tell(), None
                )
        
        # 为所有图片生成高质量的展示图片（用于画廊页面）
        if self.image and hasattr(self.image, 'name'):
            img = Image.open(self.image)
            # Convert RGBA to RGB for JPEG compatibility
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            
            # 增大展示图尺寸以提高画廊页面图片清晰度
            output_size = (600, 600)
            img.thumbnail(output_size, Image.Resampling.LANCZOS)
            buffer = BytesIO()
            # 使用最高质量保存展示图，添加subsampling=0以进一步提高质量
            img.save(buffer, format='JPEG', quality=100, optimize=False, subsampling=0)
            buffer.seek(0)
            self.display_image = InMemoryUploadedFile(
                buffer, 'ImageField', os.path.basename(self.image.name),
                'image/jpeg', buffer.tell(), None
            )
        
        super().save(*args, **kwargs)

class Album(models.Model):
    title = models.CharField(max_length=200)
    
    description = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(CrawlerUser, on_delete=models.CASCADE, related_name='crawler_albums', null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class CrawlerPinnedConversation(models.Model):
    """用户置顶的对话"""
    user_profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='pinned_conversation_records')
    other_user = models.ForeignKey(CrawlerUser, on_delete=models.CASCADE, related_name='crawler_pinned_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_profile', 'other_user')

class UserProfile(models.Model):
    user = models.OneToOneField(CrawlerUser, on_delete=models.CASCADE, related_name='crawler_userprofile')
    pinned_conversations = models.ManyToManyField(
        CrawlerUser, 
        through='CrawlerPinnedConversation',
        through_fields=('user_profile', 'other_user'),
        related_name='crawler_userprofile_pinned_in_profiles'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # 添加本地头像字段
    avatar_url = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"