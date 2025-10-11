from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from .models import Payment, Refund
from .services import alipay_service
from event.models import EventRegistration, RefundRequest
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def create_payment(request, registration_id):
    """
    创建支付订单
    
    Args:
        registration_id (int): 活动报名ID
    """
    registration = get_object_or_404(
        EventRegistration, 
        id=registration_id, 
        user=request.user
    )
    
    # 检查是否已存在支付记录
    payment, created = Payment.objects.get_or_create(
        registration=registration,
        defaults={
            'amount': registration.session.model.fee,
            'out_trade_no': '',  # 将在支付宝调用中生成
        }
    )
    
    if not created and payment.status == 'success':
        # 如果支付已成功，直接跳转到成功页面
        messages.info(request, '该订单已支付成功')
        return redirect('pay:payment_success', payment_id=payment.id)
    
    # 调用支付宝创建支付订单
    subject = f"活动报名费 - {registration.session.model.event.title}"
    result = alipay_service.create_payment(
        amount=payment.amount,
        subject=subject,
        registration_id=registration.id  # 使用对象属性而非同名参数
    )
    
    if result['success']:
        # 更新支付记录
        payment.out_trade_no = result['out_trade_no']
        payment.qr_code = result['qr_code']
        payment.save()
        
        context = {
            'payment': payment,
            'qr_code': result['qr_code'],
            'amount': payment.amount,
        }
        return render(request, 'pay/payment_qr.html', context)
    else:
        messages.error(request, f"创建支付订单失败: {result['message']}")
        return redirect('event:event_detail', pk=registration.session.model.event.id)


@login_required
def payment_success(request, payment_id):
    """
    支付成功页面
    """
    payment = get_object_or_404(Payment, id=payment_id, registration__user=request.user)
    
    context = {
        'payment': payment,
    }
    return render(request, 'pay/payment_success.html', context)


@login_required
def payment_status(request, payment_id):
    """
    查询支付状态（AJAX接口）
    """
    payment = get_object_or_404(Payment, id=payment_id, registration__user=request.user)
    
    # 调用支付宝查询支付状态
    result = alipay_service.query_payment_status(out_trade_no=payment.out_trade_no)
    
    if result['success'] and result['trade_status'] == 'TRADE_SUCCESS':
        # 更新支付状态
        payment.status = 'success'
        payment.alipay_trade_no = result['trade_no']
        payment.paid_at = timezone.now()
        payment.save()
        
        # 更新报名状态（如果需要）
        registration = payment.registration
        # 这里可以添加其他业务逻辑
        
        return JsonResponse({
            'success': True,
            'status': 'success',
            'message': '支付成功'
        })
    else:
        return JsonResponse({
            'success': False,
            'status': payment.status,
            'message': result.get('message', '支付未完成')
        })


@csrf_exempt
@require_POST
def alipay_notify(request):
    """
    支付宝异步通知接口
    """
    if request.method == 'POST':
        try:
            # 获取支付宝POST数据
            data = request.POST.dict()
            
            # 验证签名
            is_valid = alipay_service.verify_notification(data, request.GET.dict())
            
            if is_valid:
                # 处理不同的通知类型
                if data.get('trade_status') == 'TRADE_SUCCESS':
                    out_trade_no = data.get('out_trade_no')
                    
                    try:
                        with transaction.atomic():
                            # 更新支付记录
                            payment = Payment.objects.select_for_update().get(
                                out_trade_no=out_trade_no
                            )
                            
                            if payment.status != 'success':
                                payment.status = 'success'
                                payment.alipay_trade_no = data.get('trade_no')
                                payment.paid_at = timezone.now()
                                payment.save()
                                
                                # 更新报名状态为已支付
                                registration = payment.registration
                                registration.is_paid = True
                                registration.save()
                                
                                logger.info(f"Payment {out_trade_no} updated to success")
                                
                    except Payment.DoesNotExist:
                        logger.error(f"Payment with out_trade_no {out_trade_no} not found")
                        return HttpResponse('fail')
                        
                # 处理退款通知
                elif data.get('refund_status') == 'REFUND_SUCCESS':
                    # 处理退款成功的通知
                    pass
                    
                # 返回成功响应给支付宝
                return HttpResponse('success')
            else:
                logger.error("Alipay notification signature verification failed")
                return HttpResponse('fail')
                
        except Exception as e:
            logger.error(f"Error processing alipay notification: {e}")
            return HttpResponse('error')
    
    return HttpResponse('fail')


def initiate_refund(request, refund_request_id):
    """
    发起退款
    
    Args:
        refund_request_id (int): 退款申请ID
    """
    refund_request = get_object_or_404(RefundRequest, id=refund_request_id)
    
    # 检查权限（申请人或管理员）
    if request.user != refund_request.registration.user and not request.user.is_staff:
        messages.error(request, '您没有权限执行此操作')
        return redirect('event:my_events')
    
    # 检查是否已存在退款记录
    refund, created = Refund.objects.get_or_create(
        refund_request=refund_request,
        defaults={
            'amount': refund_request.amount,
            'out_refund_no': '',  # 将在支付宝调用中生成
        }
    )
    
    if not created and refund.status == 'success':
        messages.info(request, '该退款已处理完成')
        return redirect('event:my_events')
    
    # 获取对应的支付记录
    try:
        payment = refund_request.registration.payment
    except Payment.DoesNotExist:
        messages.error(request, '未找到对应的支付记录')
        return redirect('event:my_events')
    
    # 调用支付宝退款接口
    result = alipay_service.refund_payment(
        out_trade_no=payment.out_trade_no,
        refund_amount=refund.amount,
        refund_reason=refund_request.reason
    )
    
    if result['success']:
        # 更新退款记录
        refund.out_refund_no = result['out_refund_no']
        refund.status = 'success'
        refund.refunded_at = timezone.now()
        refund.save()
        
        # 更新退款申请状态
        refund_request.status = 'approved'
        refund_request.processed_at = timezone.now()
        refund_request.processed_by = request.user if request.user.is_staff else None
        refund_request.save()
        
        # 更新报名记录的退款状态
        refund_request.registration.is_refunded = True
        refund_request.registration.save()
        
        messages.success(request, '退款成功')
    else:
        refund.status = 'failed'
        refund.save()
        
        messages.error(request, f"退款失败: {result['message']}")
    
    return redirect('event:my_events')


def test_payment(request):
    """
    测试支付流程的视图（仅用于开发测试）
    """
    context = {
        'test_amount': 100.00,
        'test_subject': '测试支付订单'
    }
    return render(request, 'pay/test_payment.html', context)