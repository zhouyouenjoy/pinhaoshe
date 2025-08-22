from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    为表单字段添加CSS类的自定义过滤器
    """
    return field.as_widget(attrs={"class": css_class})