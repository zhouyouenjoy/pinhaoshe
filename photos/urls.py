# 从django.urls模块导入path函数，用于定义URL模式
from django.urls import path
# 从当前应用的views模块导入视图函数
from . import views
# 从my_space_views导入视图函数
from .my_space_views import my_info, user_albums, user_liked_photos, user_favorited_photos, user_viewed_photos, edit_profile, check_username

app_name = 'photos'

# urlpatterns是URL模式的列表，定义了URL与视图函数的映射关系
urlpatterns = [
    # 网站根路径，调用gallery视图函数，名称为gallery
    # 例如访问http://127.0.0.1:8000/会调用gallery函数
    path('', views.gallery, name='gallery'),
    
    # 搜索路径
    path('search/', views.search, name='search'),
    
    # 上传照片路径，调用upload_photo视图函数，名称为upload_photo
    # 例如访问http://127.0.0.1:8000/upload/会调用upload_photo函数,
    
    # 懒加载评论路径
    path('load-more-comments/', views.load_more_comments, name='load_more_comments'),
    path('upload/', views.upload_photo, name='upload_photo'),
    
    # 照片详情路径，包含一个整数类型的参数pk(主键)，调用photo_detail视图函数，名称为photo_detail
    # 例如访问http://127.0.0.1:8000/photo/1/会调用photo_detail函数，并传入pk=1
    path('photo/<int:pk>/', views.photo_detail, name='photo_detail'),
    path('album/<int:pk>/', views.album_detail, name='album_detail'),
    
    # 用户相册路径
    path('user/<int:user_id>/albums/', user_albums, name='user_albums'),
    
    # 我的照片路径，调用my_photos视图函数，名称为my_photos
    # 例如访问http://127.0.0.1:8000/my-photos/会调用my_photos函数
    path('my-photos/', views.my_photos, name='my_photos'),
    
    # 我的信息路径
    path('my-info/', my_info, name='my_info'),
    path('user/<int:user_id>/', my_info, name='my_info_with_id'),
    
    # 编辑资料路径
    path('edit-profile/', edit_profile, name='edit_profile'),
    
    # 检查用户名是否可用
    path('check-username/', check_username, name='check_username'),
    
    # 关注用户的最新相册路径
    path('following-albums/', views.following_albums, name='following_albums'),

    # 删除照片路径
    path('delete-photo/<int:photo_id>/', views.delete_photo, name='delete_photo'),
    
    # 删除相册路径
    path('delete-album/<int:album_id>/', views.delete_album, name='delete_album'),
    
    # 用户注册路径，调用register视图函数，名称为register
    path('register/', views.register, name='register'),
    
    # 自定义登录路径，调用custom_login视图函数
    path('accounts/login/', views.custom_login, name='login'),
    
    # 搜索用户路径
    path('search-users/', views.search_users, name='search_users'),
    
    # 微信登录路径
    path('wechat/login/', views.wechat_login, name='wechat_login'),
    # path('wechat/callback/', views.wechat_callback, name='wechat_callback'),
    
    # 获取照片评论（用于局部刷新）
    path('photo/<int:photo_id>/comments/', views.get_comment_tree, name='get_comment_tree'),
    
    # 评论相关路径
    path('photo/<int:photo_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('comment/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # 点赞相关路径
    path('photo/<int:photo_id>/like/', views.toggle_like, name='toggle_like'),
    
    # 收藏相关路径
    path('photo/<int:photo_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # 关注相关路径
    path('toggle-follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    
    # 点赞的照片
    path('liked-photos/', views.liked_photos, name='liked_photos'),
    path('user/<int:user_id>/liked-photos/', user_liked_photos, name='user_liked_photos'),
    
    # 收藏的照片
    path('favorited-photos/', views.favorited_photos, name='favorited_photos'),
    path('user/<int:user_id>/favorited-photos/', user_favorited_photos, name='user_favorited_photos'),
    
    # 浏览历史
    path('viewed-photos/', views.viewed_photos, name='viewed_photos'),
    path('user/<int:user_id>/viewed-photos/', user_viewed_photos, name='user_viewed_photos'),
    
    # 私信相关路径
    path('send-message/<int:recipient_id>/', views.send_message, name='send_message'),
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('chat/<int:recipient_id>/', views.chat_view, name='chat_view'),
    path('load-more-messages/', views.load_more_messages, name='load_more_messages'),
    path('check-new-messages/', views.check_new_messages, name='check_new_messages'),
    
    # 通知相关路径
    path('notification/<int:notification_id>/mark-as-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    
    # 批量标记私信为已读
    path('mark-messages-as-read/', views.mark_messages_as_read, name='mark_messages_as_read'),
    
    # 标记单条私信为已读
    path('message/<int:message_id>/mark-as-read/', views.mark_message_as_read, name='mark_message_as_read'),
    
    # 置顶对话
    path('pin-conversation/<int:user_id>/', views.pin_conversation, name='pin_conversation'),
    
    # 删除对话
    path('delete-conversation/<int:user_id>/', views.delete_conversation, name='delete_conversation'),
]