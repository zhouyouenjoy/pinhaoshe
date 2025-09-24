from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import os

class Album(models.Model):
    title = models.CharField(max_length=200)
    
    description = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class PinnedConversation(models.Model):
    """用户置顶的对话"""
    user_profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='pinned_conversation_records')
    other_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinned_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_profile', 'other_user')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pinned_conversations = models.ManyToManyField(
        User, 
        through='PinnedConversation',
        through_fields=('user_profile', 'other_user'),
        related_name='pinned_in_profiles'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # 如果用户上传了头像，则处理头像
        if self.avatar:
            img = Image.open(self.avatar)
            
            # 转换RGBA模式为RGB模式以支持JPEG
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            
            # 调整头像大小为300x300
            output_size = (300, 300)
            img.thumbnail(output_size, Image.Resampling.LANCZOS)
            
            # 保存处理后的头像
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)
            
            self.avatar = InMemoryUploadedFile(
                buffer, 'ImageField', os.path.basename(self.avatar.name),
                'image/jpeg', buffer.tell(), None
            )
            
            super().save(*args, **kwargs)


# 关注关系模型
class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"


class Photo(models.Model):
    image = models.ImageField(upload_to='photos/', blank=True, null=True)
    display_image = models.ImageField(upload_to='photos/display/', blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)  # 添加外部链接字段
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    approved = models.BooleanField(default=False)
    
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        if self.album:
            return f"Photo in {self.album.title}"
        else:
            return f"Photo {self.id}"
    
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


# 评论模型
class Comment(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    def __str__(self):
        return f'{self.user.username} - {self.photo.title}'
    
    def get_like_count(self):
        return self.comment_likes.count()


# 评论点赞模型
class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('comment', 'user')  # 确保一个用户只能对一条评论点赞一次
    
    def __str__(self):
        return f'{self.user.username} likes comment {self.comment.id}'


# 点赞模型
class Like(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('photo', 'user')  # 确保一个用户只能对一张照片点赞一次
    
    def __str__(self):
        return f'{self.user.username} - {self.photo.title}'


# 收藏模型
class Favorite(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('photo', 'user')  # 确保一个用户只能收藏一张照片一次
    
    def __str__(self):
        return f'{self.user.username} - {self.photo.title}'


# 浏览历史模型
class ViewHistory(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-viewed_at']  # 按浏览时间倒序排列
        unique_together = ('photo', 'user')  # 确保一个用户对一张照片只有一条浏览记录
    
    def __str__(self):
        return f'{self.user.username} - {self.photo.external_url}'


# 私信模型
class PrivateMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}: {self.content[:30]}..."


# 通知模型
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('message', 'Message'),
        ('mention', 'Mention'),
        ('favorite', 'Favorite'),
        ('comment_like', 'Comment Like'),
        ('reply', 'Reply'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_object_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"To {self.recipient.username}: {self.content[:30]}..."
    
    def get_related_object(self):
        """
        根据通知类型和related_object_id获取相关对象
        """
        if not self.related_object_id:
            return None
            
        try:
            if self.notification_type == 'like':
                return Like.objects.get(id=self.related_object_id)
            elif self.notification_type == 'comment':
                return Comment.objects.get(id=self.related_object_id)
            elif self.notification_type == 'favorite':
                return Favorite.objects.get(id=self.related_object_id)
            elif self.notification_type == 'follow':
                return Follow.objects.get(id=self.related_object_id)
            elif self.notification_type == 'mention':
                return Comment.objects.get(id=self.related_object_id)
            elif self.notification_type == 'comment_like':
                return CommentLike.objects.get(id=self.related_object_id)
            elif self.notification_type == 'reply':
                return Comment.objects.get(id=self.related_object_id)
        except (Like.DoesNotExist, Comment.DoesNotExist, Favorite.DoesNotExist, Follow.DoesNotExist, CommentLike.DoesNotExist):
            return None
        
        return None