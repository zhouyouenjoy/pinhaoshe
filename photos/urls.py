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
    path('album/<int:pk>/', views.album_detail, name='album_detail'),
    
    # 用户相册路径
    path('user/<int:user_id>/albums/', views.user_albums, name='user_albums'),
    
    # 我的照片路径，调用my_photos视图函数，名称为my_photos
    # 例如访问http://127.0.0.1:8000/my-photos/会调用my_photos函数
    path('my-photos/', views.my_photos, name='my_photos'),
    
    # 我的信息路径
    path('my-info/', views.my_info, name='my_info'),
    
    # 删除照片路径
    path('delete-photo/<int:photo_id>/', views.delete_photo, name='delete_photo'),
    
    # 用户注册路径，调用register视图函数，名称为register
    path('register/', views.register, name='register'),
    
    # 自定义登录路径，调用custom_login视图函数
    path('accounts/login/', views.custom_login, name='login'),
    
    # 微信登录路径
    path('wechat/login/', views.wechat_login, name='wechat_login'),
    path('wechat/callback/', views.wechat_callback, name='wechat_callback'),
    
    # 获取照片评论（用于局部刷新）
    path('photo/<int:photo_id>/comments/', views.get_photo_comments, name='get_photo_comments'),
    
    # 评论点赞相关路径
    path('comment/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    
    # 评论相关路径
    path('photo/<int:photo_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    
    # 点赞相关路径
    path('photo/<int:photo_id>/like/', views.toggle_like, name='toggle_like'),
    
    # 收藏相关路径
    path('photo/<int:photo_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # 关注相关路径
    path('toggle-follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    
    # 点赞、收藏、浏览历史的详细页面
    path('liked-photos/', views.liked_photos, name='liked_photos'),
    path('favorited-photos/', views.favorited_photos, name='favorited_photos'),
    path('viewed-photos/', views.viewed_photos, name='viewed_photos'),
]