from django import template

register = template.Library()

@register.filter
def is_liked_by(photo, user):
    """
    检查照片是否被用户点赞
    用法: {% if photo|is_liked_by:user %} ... {% endif %}
    """
    if user.is_authenticated:
        return photo.likes.filter(user=user).exists()
    return False