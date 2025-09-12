from django.urls import path
from . import views

app_name = 'event'
urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('create/', views.create_event, name='create_event'),
    # path('search-users/', views.search_users, name='search_users'),  # 移除这行，因为search_users在photos应用中
]