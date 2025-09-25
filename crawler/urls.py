from django.urls import path
from . import views

app_name = 'crawler'

urlpatterns = [
    path('', views.crawl_page, name='crawl_page'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('albums/<int:album_id>/', views.album_detail, name='album_detail'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('albums/<int:album_id>/delete/', views.delete_album, name='delete_album'),
    path('sync-users/', views.sync_users, name='sync_users'),
    path('check-user-status/', views.check_user_status, name='check_user_status'),  # 添加检查用户状态的URL
    path('album/<int:album_id>/photos/', views.album_photos, name='album_photos'),
    path('set-avatar/<int:user_id>/<int:photo_id>/', views.set_user_avatar, name='set_user_avatar'),
]