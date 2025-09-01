from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter
def natural_time(value):
    """
    将日期时间转换为相对时间格式（如：5分钟前，2小时前等）
    """
    if not value:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "刚刚"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}分钟前"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}小时前"
    elif seconds < 2592000:  # 30天
        days = int(seconds // 86400)
        return f"{days}天前"
    else:
        # 超过30天显示具体日期
        return value.strftime("%Y-%m-%d")