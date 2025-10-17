from django.urls import path
from . import views

app_name = 'pay'

urlpatterns = [
    # 创建支付订单
    path('create/<int:registration_id>/', views.create_payment, name='create_payment'),
    
    # 支付成功页面
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    
    # 查询支付状态（AJAX）
    path('status/<int:payment_id>/', views.payment_status, name='payment_status'),
    
    # Z-Pay异步通知
    path('zpay/notify/', views.zpay_notify, name='zpay_notify'),
    
    # 发起退款
    path('refund/<int:refund_request_id>/', views.initiate_refund, name='initiate_refund'),
    
    # 测试支付页面
    path('test/', views.test_payment_page, name='test_payment_page'),
    
    # 测试支付功能
    path('test/payment/', views.test_payment, name='test_payment'),
]