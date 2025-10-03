from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Event, EventModel, EventSession
from django.contrib.auth.models import User

# 自定义多文件上传控件
class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class EventForm(forms.ModelForm):
    # 活动时间字段
    event_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            },
            format='%Y-%m-%dT%H:%M'  # 添加格式化参数
        ),
        label='活动时间',
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True
    )
    
    # 添加隐藏字段用于存储POI信息
    location_poi = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    # 添加隐藏字段用于存储场地用户ID
    location_user = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = Event
        fields = ['title', 'event_time', 'location', 'location_poi', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '请输入活动标题'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '请输入活动地点或搜索添加',
                'data-type': 'location'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': '请输入活动详细介绍'
            }),
        }
        labels = {
            'title': '活动标题',
            'location': '活动地点',
            'description': '活动介绍',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果实例存在且event_time有值，将其格式化为datetime-local需要的格式
        if self.instance and self.instance.pk and self.instance.event_time:
            self.initial['event_time'] = self.instance.event_time.strftime('%Y-%m-%dT%H:%M')
            
        # 如果实例存在且有地点信息，初始化地点相关字段
        if self.instance and self.instance.pk:
            # 初始化POI信息
            if self.instance.location_poi:
                self.initial['location_poi'] = self.instance.location_poi
                
            # 初始化场地用户ID
            if self.instance.location_user:
                self.initial['location_user'] = self.instance.location_user.id

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 不在这里处理location_user，因为需要User实例而不是字符串
        # 从cleaned_data中移除location_user
        if 'location_user' in self.cleaned_data:
            del self.cleaned_data['location_user']
            
        if commit:
            instance.save()
        return instance


class EventModelForm(forms.Form):
    """活动模特表单"""
    model_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control model-name',
            'placeholder': '输入或搜索添加',
            'data-type': 'model'
        }),
        label='模特姓名'
    )
    
    model_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control model-fee',
            'placeholder': '模特费用'
        }),
        label='模特费用'
    )
    
    # 模特照片字段（支持多图上传）
    model_images = MultipleFileField(
        label='模特照片',
        help_text='可以上传多张模特照片',
        required=False
    )
    
    # 模特服装图片字段（支持多图上传）
    outfit_images = MultipleFileField(
        label='服装图片',
        help_text='可以上传多张模特服装图片',
        required=False
    )
    
    # 拍摄场景图片字段（支持多图上传）
    scene_images = MultipleFileField(
        label='拍摄场景',
        help_text='可以上传多张拍摄场景图片',
        required=False
    )


class EventSessionForm(forms.Form):
    """活动场次表单"""
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control start-time',
            'type': 'time',
            'placeholder': '开始时间'
        }),
        label='开始时间'
    )
    
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control end-time',
            'type': 'time',
            'placeholder': '结束时间'
        }),
        label='结束时间'
    )
