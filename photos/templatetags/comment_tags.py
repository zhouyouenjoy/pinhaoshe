from django import template
from django.template.loader import render_to_string
from operator import attrgetter

register = template.Library()

@register.filter
def slice_replies(replies, limit=1):
    """
    获取指定数量的回复评论
    用法: {{ comment.replies.all|slice_replies:5 }}
    """
    if hasattr(replies, 'all'):
        replies_list = list(replies.all())
    else:
        replies_list = list(replies)
    
    # 按照创建时间倒序排序
    replies_list.sort(key=attrgetter('created_at'), reverse=True)
    return replies_list[:limit]

@register.filter
def count_replies(replies):
    """
    获取回复评论的总数
    用法: {{ comment.replies.all|count_replies }}
    """
    if hasattr(replies, 'count'):
        return replies.count()
    elif hasattr(replies, 'all'):
        return len(list(replies.all()))
    else:
        return len(list(replies))

@register.filter
def has_more_replies(replies, shown_count):
    """
    检查是否还有更多回复未显示
    用法: {{ comment.replies.all|count_replies|add:"-1" }}
    """
    total_count = count_replies(replies)
    return total_count > shown_count