from django import forms
from .models import Event
from django.contrib.auth.models import User

class EventForm(forms.ModelForm):
    # 重写model_name字段，使其支持多个模特
    model_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '可以输入多位模特，用逗号分隔'}),
        label='活动模特',
        help_text='可以输入多位模特，用逗号分隔'
    )
    
    # 活动时间字段
    event_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }
        ),
        label='活动时间'
    )
    
    class Meta:
        model = Event
        fields = ['title', 'model_name', 'event_time', 'location', 'fee', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入活动标题'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入活动场地'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入活动费用'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '请输入活动详细介绍'}),
        }
        labels = {
            'title': '活动标题',
            'location': '活动场地',
            'fee': '活动费用',
            'description': '活动介绍',
        }