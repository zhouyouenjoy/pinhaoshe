# 从django.urls模块导入path函数，用于定义URL模式
from django.urls import path
# 从当前应用的views模块导入视图函数
from . import views

# urlpatterns是URL模式的列表，定义了URL与视图函数的映射关系
urlpatterns = [
    # 网站根路径，调用gallery视图函数，名称为gallery
    # 例如访问http://127.0.0.1:8000/会调用gallery函数
    path('', views.gallery, name='gallery'),
    
    # 上传照片路径，调用upload_photo视图函数，名称为upload_photo
    # 例如访问http://127.0.0.1:8000/upload/会调用upload_photo函数
    path('upload/', views.upload_photo, name='upload_photo'),
    
    # 照片详情路径，包含一个整数类型的参数pk(主键)，调用photo_detail视图函数，名称为photo_detail
    # 例如访问http://127.0.0.1:8000/photo/1/会调用photo_detail函数，并传入pk=1
    path('photo/<int:pk>/', views.photo_detail, name='photo_detail'),
    
    # 我的照片路径，调用my_photos视图函数，名称为my_photos
    # 例如访问http://127.0.0.1:8000/my-photos/会调用my_photos函数
    path('my-photos/', views.my_photos, name='my_photos'),
    
    # 用户注册路径，调用register视图函数，名称为register
    path('register/', views.register, name='register'),
    
    # 自定义登录路径，调用custom_login视图函数
    path('accounts/login/', views.custom_login, name='login'),
]