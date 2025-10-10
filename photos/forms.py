# 从django模块导入forms，用于创建表单
from django import forms
# 从当前应用的models模块导入Photo和UserProfile模型
from .models import Photo, UserProfile
from django.contrib.auth.models import User

# 定义PhotoForm表单类，继承自ModelForm
# ModelForm可以根据模型自动生成表单
class PhotoForm(forms.ModelForm):
    # Meta类用于配置ModelForm的行为
    class Meta:
        # 指定关联的模型为Photo
        model = Photo
        # 指定表单包含的字段，这里只包含图片字段
        fields = ['image']
        # 定义字段的小部件（前端显示样式）
        widgets = {
            # 为图片字段使用Bootstrap的form-control样式
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

# 用户注册表单
class UserRegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        label='用户名'
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
        label='邮箱地址'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm'}),
        label='密码'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm'}),
        label='确认密码'
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        label='头像'
    )
    
    def clean_username(self):
        username = self.cleaned_data['username']
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("用户名已存在")
        return username
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("两次输入的密码不一致")
        return password2

# 用户空间表单（用于修改用户信息）
class UserSpaceForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']
        labels = {
            'avatar': '头像'
        }
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserSpaceForm, self).__init__(*args, **kwargs)
        
        # 添加额外字段
        self.fields['username'] = forms.CharField(
            max_length=150,
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            label='用户名'
        )
        self.fields['email'] = forms.EmailField(
            required=False,
            widget=forms.EmailInput(attrs={'class': 'form-control'}),
            label='邮箱地址'
        )
        
        # 初始化表单字段的初始值
        if self.user:
            self.fields['username'].initial = self.user.username
            if hasattr(self.user, 'userprofile'):
                self.fields['email'].initial = self.user.userprofile.email
                self.fields['avatar'].initial = self.user.userprofile.avatar

    def clean_username(self):
        """验证用户名唯一性，排除当前用户本身"""
        username = self.cleaned_data['username']
        if self.user and User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("用户名已存在")
        return username

    def save(self, commit=True):
        # 获取或创建UserProfile实例
        if not self.instance.pk and self.user:
            # 尝试获取现有的UserProfile，如果不存在则创建新的
            user_profile, created = UserProfile.objects.get_or_create(user=self.user)
            self.instance = user_profile
        
        user_profile = super().save(commit=False)
        
        # 更新关联的 User 对象
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        
        # 处理头像更新
        if 'avatar' in self.cleaned_data:
            user_profile.avatar = self.cleaned_data['avatar']
        
        if commit:
            user_profile.save()
        return user_profile
