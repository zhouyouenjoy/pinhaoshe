from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Event(models.Model):
    """摄影活动模型"""
    title = models.CharField(max_length=200, verbose_name="活动标题")
    description = models.TextField(verbose_name="活动描述")
    model_name = models.CharField(max_length=100, verbose_name="活动模特")
    event_time = models.DateTimeField(verbose_name="活动时间")
    location = models.CharField(max_length=200, verbose_name="活动场地")
    fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="活动费用")
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