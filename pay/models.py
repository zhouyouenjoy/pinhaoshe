from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from event.models import EventRegistration, RefundRequest


class Payment(models.Model):
    """支付订单模型"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待支付'),
        ('success', '支付成功'),
        ('failed', '支付失败'),
        ('closed', '已关闭'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('alipay_qr', '支付宝扫码支付'),
        ('wechat_pay', '微信支付'),
        ('bank_transfer', '银行转账'),
    ]
    
    # 关联报名记录
    registration = models.OneToOneField(
        EventRegistration, 
        on_delete=models.CASCADE, 
        related_name='payment',
        verbose_name="活动报名"
    )
    
    # 支付金额
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="支付金额"
    )
    
    # 支付状态
    status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending', 
        verbose_name="支付状态"
    )
    
    # 支付方式
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='alipay_qr', 
        verbose_name="支付方式"
    )
    
    # 支付宝交易号（支付宝返回）
    alipay_trade_no = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="支付宝交易号"
    )
    
    # 商户订单号（我们生成）
    out_trade_no = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="商户订单号"
    )
    
    # 二维码内容（用于扫码支付）
    qr_code = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="二维码内容"
    )
    
    # 创建时间
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="创建时间"
    )
    
    # 支付完成时间
    paid_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="支付完成时间"
    )
    
    class Meta:
        verbose_name = "支付订单"
        verbose_name_plural = "支付订单"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.out_trade_no} - {self.amount} - {self.status}"


class Refund(models.Model):
    """退款记录模型"""
    REFUND_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '退款中'),
        ('success', '退款成功'),
        ('failed', '退款失败'),
    ]
    
    # 关联退款申请
    refund_request = models.OneToOneField(
        RefundRequest, 
        on_delete=models.CASCADE, 
        related_name='refund_record',
        verbose_name="退款申请"
    )
    
    # 退款金额
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="退款金额"
    )
    
    # 退款状态
    status = models.CharField(
        max_length=20, 
        choices=REFUND_STATUS_CHOICES, 
        default='pending', 
        verbose_name="退款状态"
    )
    
    # 支付宝退款交易号
    alipay_refund_no = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="支付宝退款交易号"
    )
    
    # 商户退款单号
    out_refund_no = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="商户退款单号"
    )
    
    # 创建时间
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="创建时间"
    )
    
    # 退款完成时间
    refunded_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="退款完成时间"
    )
    
    class Meta:
        verbose_name = "退款记录"
        verbose_name_plural = "退款记录"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.out_refund_no} - {self.amount} - {self.status}"