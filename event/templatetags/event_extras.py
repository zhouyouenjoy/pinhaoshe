from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

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
def event_datetime_display(event):
    """
    返回活动时间显示文本（如"明天 14:00"）
    """
    now = timezone.now()
    event_date = event.event_time.date()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    
    if event_date == today:
        return f"今天 {event.event_time.strftime('%H:%M')}"
    elif event_date == tomorrow:
        return f"明天 {event.event_time.strftime('%H:%M')}"
    else:
        return event.event_time.strftime('%Y-%m-%d %H:%M')

@register.filter
def needs_reminder(event):
    """
    判断是否需要提醒（这里简单返回True，实际可以根据活动内容判断）
    """
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
def get_item(dictionary, key):
    """
    从字典中获取指定键的值
    """
    return dictionary.get(key)
