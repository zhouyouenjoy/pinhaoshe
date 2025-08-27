from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    为表单字段添加CSS类的自定义过滤器
    """
    return field.as_widget(attrs={"class": css_class})

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