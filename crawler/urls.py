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
    path('sync-users/', views.sync_users, name='sync_users'),  # 添加同步用户数据的URL
]