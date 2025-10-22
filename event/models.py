from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


class Event(models.Model):
    """摄影活动模型"""
    STATUS_CHOICES = [
        ('pending', '待开始'),
        ('ongoing', '进行中'),
        ('finished', '已结束'),
        ('cancelled', '已取消'),
    ]
    
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="活动状态")
    
    class Meta:
        verbose_name = "摄影活动"
        verbose_name_plural = "摄影活动"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('event:event_detail', kwargs={'pk': self.pk})
    
    def get_participant_count(self):
        """获取活动参与者数量（排除已退款和未支付的参与者）"""
        from .models import EventRegistration
        from django.utils import timezone
        from datetime import timedelta
        
        # 计算3分钟前的时间点
        three_minutes_ago = timezone.now() - timedelta(minutes=3)
        
        # 只统计已支付的或未支付但在3分钟内的报名
        return EventRegistration.objects.filter(
            session__model__event=self,
            is_refunded=False
        ).filter(
            models.Q(is_paid=True) |  # 已支付的
            models.Q(is_paid=False, registered_at__gte=three_minutes_ago)  # 未支付但在3分钟内
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
        """获取模特所有场次的已报名人数（仅计算已完成支付的报名）"""
        from .models import EventRegistration
        
        # 只统计已完成支付且未退款的报名
        return EventRegistration.objects.filter(
            session__model=self,
            is_paid=True,
            is_refunded=False
        ).count()
        
    def get_total_spots(self):
        """获取模特所有场次的总名额数"""
        return self.sessions.aggregate(total=models.Sum('photographer_count'))['total'] or 0
    
    def get_remaining_spots(self):
        """获取模特所有场次的剩余名额数"""
        total_remaining = 0
        for session in self.sessions.all():
            total_remaining += session.remaining_spots()
        return total_remaining
    
    def has_any_pending_registration(self, user):
        """检查用户是否有待支付的报名"""
        if not user.is_authenticated:
            return False
        return self.sessions.filter(
            registrations__user=user,
            registrations__is_paid=False,
            registrations__is_refunded=False
        ).exists()


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
        """获取已报名人数（仅统计已完成支付的报名）"""
        return self.registrations.filter(
            is_paid=True,
            is_refunded=False
        ).count()
        
    def remaining_spots(self):
        """获取剩余报名名额"""
        # 排除已退款的报名和已过期的未支付报名
        from django.utils import timezone
        from datetime import timedelta
        
        # 计算3分钟前的时间点
        three_minutes_ago = timezone.now() - timedelta(minutes=3)
        
        # 统计有效的报名数量（已支付的或未支付但在3分钟内的）
        valid_registrations = self.registrations.filter(
            is_refunded=False  # 排除已退款的
        ).filter(
            models.Q(is_paid=True) |  # 已支付的
            models.Q(is_paid=False, registered_at__gte=three_minutes_ago)  # 未支付但在3分钟内
        ).count()
        
        return self.photographer_count - valid_registrations
        
    def has_pending_registration(self, user):
        """检查用户是否有待支付的报名"""
        if not user.is_authenticated:
            return False
        return self.registrations.filter(
            user=user,
            is_paid=False,
            is_refunded=False
        ).exists()
        
    def get_pending_registration(self, user):
        """获取用户待支付的报名记录"""
        if not user.is_authenticated:
            return None
        try:
            return self.registrations.filter(
                user=user,
                is_paid=False,
                is_refunded=False
            ).first()
        except:
            return None


class EventRegistration(models.Model):
    """活动报名模型"""
    session = models.ForeignKey(EventSession, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="报名用户")
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="报名时间")
    is_refunded = models.BooleanField(default=False, verbose_name="是否已退款")
    is_paid = models.BooleanField(default=False, verbose_name="是否已支付")
    
    class Meta:
        verbose_name = "活动报名"
        verbose_name_plural = "活动报名"
        # 移除unique_together约束，允许用户对同一场次多次报名（如退款后重新报名）
        
    def __str__(self):
        return f"{self.session.model.name} - {self.session.title} - {self.user.username}"
        
    def is_pending_expired(self):
        """检查待支付是否已过期（超过3分钟）"""
        # 检查是否有关联的支付记录
        if hasattr(self, 'payment'):
            # 如果支付成功，则不是待支付状态
            if self.payment.status == 'success':
                return False
            # 如果有支付记录但未成功，检查是否过期
            expiration_time = self.registered_at + timedelta(minutes=3)
            return timezone.now() > expiration_time
        else:
            # 如果没有支付记录，使用原来的is_paid和is_refunded字段判断
            if self.is_paid or self.is_refunded:
                return False
            expiration_time = self.registered_at + timedelta(minutes=3)
            return timezone.now() > expiration_time
        
    @classmethod
    def cleanup_expired_pending_registrations(cls):
        """清理过期的待支付报名记录"""
        # 查找所有未支付且未退款的报名记录
        pending_registrations = cls.objects.filter(
            is_paid=False,
            is_refunded=False
        )
        
        count = 0
        for registration in pending_registrations:
            # 检查是否过期（超过3分钟）
            if registration.is_pending_expired():
                registration.is_refunded = True
                registration.save()
                count += 1
                
        return count


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