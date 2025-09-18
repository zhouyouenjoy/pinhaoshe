from django.urls import path
from . import views

app_name = 'crawler'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('users/', views.user_list, name='user_list'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('crawl/', views.crawl_page, name='crawl_page'),
]