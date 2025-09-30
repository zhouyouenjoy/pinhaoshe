from django.urls import path
from . import views

app_name = 'event'
urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('create/', views.create_event, name='create_event'),
    path('edit/<int:event_id>/', views.create_event, name='edit_event'),
    path('register/<int:session_id>/', views.register_session, name='register_session'),
    path('my-events/', views.my_events, name='my_events'),
    path('registrations/<int:event_id>/', views.event_registrations, name='event_registrations'),  # 添加查看报名名单的URL
    # path('search-users/', views.search_users, name='search_users'),  # 移除这行，因为search_users在photos应用中
]