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

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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


class Photo(models.Model):
    title = models.CharField(max_length=200)
    
    image = models.ImageField(upload_to='photos/')
    display_image = models.ImageField(upload_to='photos/display/', blank=True, null=True)
    
    description = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    approved = models.BooleanField(default=False)
    
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
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