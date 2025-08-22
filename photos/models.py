from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from io import BytesIO  # Add this import
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
        super().save(*args, **kwargs)
        
        img = Image.open(self.image.path)
        
        if img.height > 800 or img.width > 800:
            output_size = (800, 800)
            img.thumbnail(output_size)
            img.save(self.image.path)
        
        # 处理主图片
        if self.image and hasattr(self.image, 'name'):
            img = Image.open(self.image)
            # Convert RGBA to RGB for JPEG compatibility
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            output_size = (800, 800)
            img.thumbnail(output_size)
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            self.image = InMemoryUploadedFile(
                buffer, 'ImageField', os.path.basename(self.image.name),
                'image/jpeg', buffer.tell(), None
            )
        
        # 处理显示图片
        if self.display_image and hasattr(self.display_image, 'name'):
            img = Image.open(self.display_image)
            # Convert RGBA to RGB for JPEG compatibility
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            output_size = (300, 300)
            img.thumbnail(output_size)
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            self.display_image = InMemoryUploadedFile(
                buffer, 'ImageField', os.path.basename(self.display_image.name),
                'image/jpeg', buffer.tell(), None
            )
        
        super().save(*args, **kwargs)