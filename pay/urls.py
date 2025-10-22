from django.urls import path
from . import views

app_name = 'pay'

urlpatterns = [
    # 创建支付订单
    path('create/<int:registration_id>/', views.create_payment, name='create_payment'),
    
    # 支付成功页面
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    
    # 支付平台回调
    path('success/', views.payment_success_callback, name='payment_success_callback'),
    
    # 查询支付状态（AJAX）
    path('status/<int:payment_id>/', views.payment_status, name='payment_status'),
    
    # Z-Pay异步通知
    path('zpay/notify/', views.zpay_notify, name='zpay_notify'),
    
    # 发起退款 (仅接受POST请求)
    path('refund/<int:refund_request_id>/', views.initiate_refund, name='initiate_refund'),
]