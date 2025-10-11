from django.contrib import admin
from .models import Payment, Refund

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['out_trade_no', 'registration', 'amount', 'status', 'payment_method', 'created_at', 'paid_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['out_trade_no', 'alipay_trade_no']
    readonly_fields = ['created_at', 'paid_at']

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['out_refund_no', 'refund_request', 'amount', 'status', 'created_at', 'refunded_at']
    list_filter = ['status', 'created_at']
    search_fields = ['out_refund_no', 'alipay_refund_no']
    readonly_fields = ['created_at', 'refunded_at']