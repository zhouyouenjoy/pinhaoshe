from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Event(models.Model):
    """摄影活动模型"""
    title = models.CharField(max_length=200, verbose_name="活动标题")
    description = models.TextField(verbose_name="活动描述")
    event_time = models.DateTimeField(verbose_name="活动时间")
    location = models.CharField(max_length=200, verbose_name="活动场地")
    location_poi = models.TextField(verbose_name="活动场地POI信息", blank=True, null=True)  # 新增字段存储完整POI信息
    location_user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="场地提供者", blank=True, null=True, related_name='events_as_location')  # 添加场地用户ID字段
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
    
    def get_participant_count(self):
        """获取活动参与者数量"""
        from .models import EventRegistration
        return EventRegistration.objects.filter(
            session__model__event=self
        ).count()
        
    def get_total_spots(self):
        """获取活动总名额数"""
        total = 0
        for model in self.models.all():
            total += model.total_spots()
        return total


class EventModel(models.Model):
    """活动模特模型"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100, verbose_name="模特姓名")
    model_user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="模特用户", blank=True, null=True, related_name='events_as_model')  # 添加模特用户ID字段
    fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="模特费用")
    vip_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="VIP模特费用", blank=True, null=True)
    model_images = models.ImageField(upload_to='event_models/', verbose_name="模特照片", blank=True, null=True)
    outfit_images = models.ImageField(upload_to='event_outfits/', verbose_name="模特服装图片", blank=True, null=True)
    scene_images = models.ImageField(upload_to='event_scenes/', verbose_name="拍摄场景图片", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "活动模特"
        verbose_name_plural = "活动模特"
    
    def __str__(self):
        return f"{self.event.title} - {self.name}"
        
    def total_spots(self):
        """获取模特所有场次的总名额数"""
        return self.sessions.aggregate(total=models.Sum('photographer_count'))['total'] or 0
        
    def get_registered_count(self):
        """获取模特所有场次的已报名人数"""
        from .models import EventRegistration
        return EventRegistration.objects.filter(session__model=self).count()
        
    def get_total_spots(self):
        """获取模特所有场次的总名额数"""
        return self.sessions.aggregate(total=models.Sum('photographer_count'))['total'] or 0


class EventSession(models.Model):
    """活动场次模型"""
    model = models.ForeignKey(EventModel, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=100, verbose_name="场次标题")
    start_time = models.TimeField(verbose_name="开始时间")
    end_time = models.TimeField(verbose_name="结束时间")
    created_at = models.DateTimeField(auto_now_add=True)
    photographer_count = models.PositiveIntegerField(verbose_name="可报名人数", default=1)
    
    class Meta:
        verbose_name = "活动场次"
        verbose_name_plural = "活动场次"
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.model.name} - {self.title}"
        
    def registered_count(self):
        """获取已报名人数"""
        return self.registrations.count()
        
    def remaining_spots(self):
        """获取剩余报名名额"""
        # 排除已退款的报名
        non_refunded_registrations = self.registrations.filter(is_refunded=False).count()
        return self.photographer_count - non_refunded_registrations


class EventRegistration(models.Model):
    """活动报名模型"""
    session = models.ForeignKey(EventSession, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="报名用户")
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="报名时间")
    is_refunded = models.BooleanField(default=False, verbose_name="是否已退款")
    
    class Meta:
        verbose_name = "活动报名"
        verbose_name_plural = "活动报名"
        # 移除unique_together约束，允许用户对同一场次多次报名（如退款后重新报名）
        
    def __str__(self):
        return f"{self.session.model.name} - {self.session.title} - {self.user.username}"


class RefundRequest(models.Model):
    """退款申请模型"""
    REFUND_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]
    
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE, related_name='refund_requests')
    reason = models.TextField(verbose_name="退款原因")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="退款金额")
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending', verbose_name="状态")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="申请时间")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="处理时间")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="处理人")
    processed_reason = models.TextField(blank=True, verbose_name="处理说明")
    
    class Meta:
        verbose_name = "退款申请"
        verbose_name_plural = "退款申请"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.registration.user.username} - {self.registration.session.model.event.title} - {self.amount}"