# 从django模块导入forms，用于创建表单
from django import forms
# 从当前应用的models模块导入Photo模型
from .models import Photo

# 定义PhotoForm表单类，继承自ModelForm
# ModelForm可以根据模型自动生成表单字段
class PhotoForm(forms.ModelForm):
    # Meta类用于配置ModelForm的行为
    class Meta:
        # 指定关联的模型为Photo
        model = Photo
        # 指定表单包含的字段，这里包含标题、图片和描述三个字段
        fields = ['title', 'image', 'description']
        # 定义字段的小部件（前端显示样式）
        widgets = {
            # 为标题字段使用Bootstrap的form-control样式
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            # 为描述字段使用Bootstrap的form-control样式，并设置4行高度
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }