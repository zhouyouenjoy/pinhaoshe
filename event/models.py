from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Event(models.Model):
    """摄影活动模型"""
    title = models.CharField(max_length=200, verbose_name="活动标题")
    description = models.TextField(verbose_name="活动描述")
    event_time = models.DateTimeField(verbose_name="活动时间")
    location = models.CharField(max_length=200, verbose_name="活动场地")
    location_poi = models.TextField(verbose_name="活动场地POI信息", blank=True, null=True)  # 新增字段存储完整POI信息
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    approved = models.BooleanField(default=False, verbose_name="是否审核通过")
    
    class Meta:
        verbose_name = "摄影活动"
        verbose_name_plural = "摄影活动"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('event:event_detail', kwargs={'pk': self.pk})


class EventModel(models.Model):
    """活动模特模型"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100, verbose_name="模特姓名")
    fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="模特费用")
    model_images = models.ImageField(upload_to='event_models/', verbose_name="模特照片", blank=True, null=True)
    outfit_images = models.ImageField(upload_to='event_outfits/', verbose_name="模特服装图片", blank=True, null=True)
    scene_images = models.ImageField(upload_to='event_scenes/', verbose_name="拍摄场景图片", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "活动模特"
        verbose_name_plural = "活动模特"
    
    def __str__(self):
        return f"{self.event.title} - {self.name}"


class EventSession(models.Model):
    """活动场次模型"""
    model = models.ForeignKey(EventModel, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=100, verbose_name="场次标题")
    start_time = models.TimeField(verbose_name="开始时间")
    end_time = models.TimeField(verbose_name="结束时间")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "活动场次"
        verbose_name_plural = "活动场次"
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.model.name} - {self.title}"