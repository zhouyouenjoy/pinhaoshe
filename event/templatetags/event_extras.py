from django import template
from django.utils import timezone
from datetime import timedelta
from ..models import EventRegistration, RefundRequest  # 导入模型到顶部

register = template.Library()


@register.filter
def get_pending_registration(session, user):
    """
    获取用户在特定场次中的待支付报名记录
    
    使用方法: {{ session|get_pending_registration:user }}
    """
    if not user.is_authenticated:
        return None
    
    try:
        registration = EventRegistration.objects.filter(
            session=session,
            user=user,
            is_paid=False,
            is_refunded=False
        ).first()
        return registration
    except EventRegistration.DoesNotExist:
        return None

@register.filter
def has_pending_registration(session, user):
    """
    检查用户在特定场次中是否有有效的待支付报名记录（未过期）

    使用方法: {% if session|has_pending_registration:user %}
    """
    if not user.is_authenticated:
        return False
    
    try:
        registration = EventRegistration.objects.filter(
            session=session,
            user=user,
            is_paid=False,
            is_refunded=False
        ).first()
        
        # 如果没有待支付记录，直接返回False
        if not registration:
            return False
            
        # 如果有待支付记录，检查是否过期
        if registration.is_pending_expired():
            # 如果已过期，标记为已退款以释放名额
            registration.is_refunded = True
            registration.save()
            return False
            
        return True
    except:
        return False

@register.filter
def is_pending_expired(registration):
    """
    检查待支付报名是否已过期（超过3分钟）
    
    使用方法: {% if registration|is_pending_expired %}
    """
    if not registration:
        return False
    return registration.is_pending_expired()

@register.filter
def event_status(event):
    """
    返回活动状态: ongoing(进行中), ended(已结束), upcoming(待开始)
    """
    now = timezone.now()
    if event.event_time < now:
        # 活动时间已过，判断是否结束（假设活动持续4小时）
        if event.event_time + timedelta(hours=4) < now:
            return 'ended'
        else:
            return 'ongoing'
    else:
        return 'upcoming'

@register.filter
def event_status_display(event):
    """
    返回活动状态显示文本
    """
    status = event_status(event)
    if status == 'ongoing':
        return '进行中'
    elif status == 'ended':
        return '已结束'
    else:
        return '待开始'

@register.filter
def event_status_color(event):
    """
    返回活动状态对应的Bootstrap颜色类
    """
    status = event_status(event)
    if status == 'ongoing':
        return 'success'  # 绿色
    elif status == 'ended':
        return 'secondary'  # 灰色
    else:
        return 'info'  # 蓝色（待开始）

@register.filter
def can_edit_event(event):
    """
    判断活动是否可以编辑
    活动开始前24小时内不得编辑
    """
    now = timezone.now()
    time_diff = event.event_time - now
    
    # 如果活动已经开始或距离开始不足24小时，则不能编辑
    if time_diff <= timedelta(hours=24):
        return False
    else:
        return True

@register.filter
def can_refund(event):
    """
    判断是否可以退款
    活动前48小时可以全额退款，不足48小时大于24小时退款一半，不足24小时无法退款
    """
    now = timezone.now()
    time_diff = event.event_time - now
    
    # 大于48小时可以退款
    if time_diff > timedelta(hours=48):
        return True
    # 24-48小时之间可以部分退款
    elif time_diff > timedelta(hours=24):
        return True
    # 小于24小时无法退款
    else:
        return False

@register.filter
def get_pending_refund_count(event, user):
    """
    获取活动待处理的退款申请数量
    """
    try:
        # 获取该活动创建者的所有待处理退款申请数量
        count = RefundRequest.objects.filter(
            registration__session__model__event=event,
            registration__session__model__event__created_by=user,
            status='pending'
        ).count()
        return count
    except:
        return 0

@register.filter
def get_registration_refund_status(registration):
    """
    获取特定注册的退款状态
    返回退款申请的状态，如果没有退款申请则返回None
    如果注册已被标记为已退款，则返回'approved'
    """
    try:
        # 如果注册已被标记为已退款，直接返回已批准状态
        if registration.is_refunded:
            return 'approved'
            
        refund_request = RefundRequest.objects.filter(
            registration=registration
        ).order_by('-created_at').first()
        
        if refund_request:
            return refund_request.status
        else:
            return None
    except:
        return None

@register.filter
def is_pending_payment(registration):
    """
    检查报名是否处于待付款状态（已报名但未付款，且未过期）
    """
    # 检查是否有关联的支付记录
    if hasattr(registration, 'payment'):
        # 如果支付成功或已退款，则不是待付款状态
        if registration.payment.status == 'success' or registration.is_refunded:
            return False
            
        # 检查是否超时（超过3分钟）
        if registration.is_pending_expired():
            return False
            
        # 未付款、未退款且未过期，则为待付款状态
        return True
    else:
        # 如果没有支付记录，使用原来的is_paid和is_refunded字段判断
        # 如果已经付款或已退款，则不是待付款状态
        if registration.is_paid or registration.is_refunded:
            return False
            
        # 检查是否超时（超过3分钟）
        if registration.is_pending_expired():
            return False
            
        # 未付款、未退款且未过期，则为待付款状态
        return True

@register.filter
def is_payment_expired(registration):
    """
    检查报名支付是否已超时（已报名但未付款，且已过期）
    """
    # 检查是否有关联的支付记录
    if hasattr(registration, 'payment'):
        # 如果支付成功或已退款，则不是支付超时状态
        if registration.payment.status == 'success' or registration.is_refunded:
            return False
    else:
        # 如果没有支付记录，使用原来的is_paid和is_refunded字段判断
        # 如果已经付款或已退款，则不是支付超时状态
        if registration.is_paid or registration.is_refunded:
            return False
    
    # 检查是否超时（超过3分钟）
    return registration.is_pending_expired()

@register.filter
def get_item(dictionary, key):
    """
    从字典中获取指定键的值
    用法: {{ dictionary|get_item:key }}
    """
    # 处理dictionary为None的情况
    if dictionary is None:
        return None
    return dictionary.get(key)
