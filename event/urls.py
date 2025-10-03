from django.urls import path
from . import views

app_name = 'event'
urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('model/<int:model_id>/album/', views.model_album, name='model_album'),
    path('create/', views.create_event, name='create_event'),
    path('<int:event_id>/edit/', views.create_event, name='edit_event'),
    path('session/<int:session_id>/register/', views.register_session, name='register_session'),
    path('register/<int:session_id>/', views.register_session, name='register_session'),  # 兼容旧URL
    path('my-events/', views.my_events, name='my_events'),
    path('<int:event_id>/registrations/', views.event_registrations, name='event_registrations'),
    path('request_refund/<int:registration_id>/', views.request_refund, name='request_refund'),
    path('my_refund_requests/', views.my_refund_requests, name='my_refund_requests'),
    path('pending_refunds/', views.pending_refunds, name='pending_refunds'),
    path('process_refund/<int:refund_id>/', views.process_refund, name='process_refund'),
]