from django import template
from photos.models import Comment

register = template.Library()

@register.filter
def get_obj_for_related_object_id(notification):
    """
    根据通知的related_object_id获取对应的对象
    """
    if not notification.related_object_id:
        return None
    
    try:
        if notification.notification_type == 'mention':
            # 对于mention类型，related_object_id是Comment的ID
            return Comment.objects.get(id=notification.related_object_id)
        # 可以添加其他类型通知的处理逻辑
        return None
    except Comment.DoesNotExist:
        return None
    except Exception:
        return None