import re
from django import template
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.urls import reverse

register = template.Library()

@register.filter
def linkify_mentions(content):
    """
    将评论内容中的@用户名转换为蓝色可点击的链接
    """
    # 如果内容为空，直接返回
    if not content:
        return content
        
    # 匹配@用户名的正则表达式 (支持中英文用户名)
    pattern = r'@([a-zA-Z0-9_.\-\u4e00-\u9fa5]+)'
    
    def replace_mention(match):
        username = match.group(1)
        try:
            # 尝试获取用户对象
            user = User.objects.get(username=username)
            # 生成用户主页的URL
            url = reverse('photos:my_info_with_id', args=[user.id])
            return f'<a href="{url}" class="text-primary">@{username}</a>'
        except User.DoesNotExist:
            # 如果用户不存在，返回原始文本
            return match.group(0)
        except Exception as e:
            # 如果出现其他错误，也返回原始文本
            return match.group(0)
    
    # 使用正则表达式替换所有匹配的@用户名
    linked_content = re.sub(pattern, replace_mention, content)
    
    # 返回安全的HTML内容
    return mark_safe(linked_content)