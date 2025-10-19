from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from .models import Payment
from .services import zpay_service  # 使用Z-Pay服务替代支付宝服务
from event.models import EventRegistration, RefundRequest
import json
import logging
import time
import random

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
    
    # 检查是否已存在支付记录且已支付成功
    existing_payment = Payment.objects.filter(registration=registration).first()
    if existing_payment and existing_payment.status == 'success':
        # 如果支付已成功，直接跳转到成功页面
        messages.info(request, '该订单已支付成功')
        return redirect('pay:payment_success', payment_id=existing_payment.id)

    # 生成临时订单号（仅用于日志）
    temp_out_trade_no = zpay_service._generate_out_trade_no()

    # 调用Z-Pay创建支付订单
    subject = f"活动报名费 - {registration.session.model.event.title}"
    logger.info(f"Calling zpay_service.create_payment with amount: {registration.session.model.fee}, subject: {subject}")
    
    # 根据支付方式选择支付类型
    payment_method_map = {
        'zpay_alipay': 'alipay',
        'zpay_wechat': 'wxpay',
        'zpay_qq': 'qqpay',
        'zpay_bank': 'bank',
    }
    pay_type = payment_method_map.get(existing_payment.payment_method if existing_payment else 'zpay_wechat', 'wxpay')
    
    try:
        result = zpay_service.create_payment(
            amount=registration.session.model.fee,
            subject=subject,
            registration_id=registration.id,
            pay_type=pay_type
        )
        
        logger.info(f"Z-Pay create payment result: {result}")
        
        if result['success']:
            # Z-Pay订单创建成功，创建或更新支付记录
            payment, created = Payment.objects.get_or_create(
                registration=registration,
                defaults={
                    'amount': registration.session.model.fee,
                    'out_trade_no': result['out_trade_no'],
                    'payment_method': existing_payment.payment_method if existing_payment else 'zpay_alipay',
                }
            )
            
            # 如果记录已存在，更新它
            if not created:
                payment.out_trade_no = result['out_trade_no']
                payment.status = 'pending'
                payment.save()
            
            logger.info(f"Payment saved with out_trade_no: {payment.out_trade_no}")
            
            # 重定向到Z-Pay支付页面
            return redirect(result['pay_url'])
        else:
            messages.error(request, f"创建支付订单失败: {result['message']}")
            return redirect('event:event_detail', pk=registration.session.model.event.id)
            
    except Exception as e:
        logger.error(f"Failed to create payment for registration {registration_id}: {e}")
        messages.error(request, '创建支付订单时发生错误，请稍后重试')
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
    logger.info(f"Checking payment status for payment_id: {payment_id}")
    payment = get_object_or_404(Payment, id=payment_id, registration__user=request.user)
    
    logger.info(f"Found payment: id={payment.id}, out_trade_no={payment.out_trade_no}, status={payment.status}")
    
    # 检查out_trade_no是否存在
    if not payment.out_trade_no:
        logger.warning(f"Payment {payment_id} has no out_trade_no")
        return JsonResponse({
            'success': False,
            'status': payment.status,
            'message': '支付订单号不存在'
        })
    
    # 检查是否是临时订单号（以TEMP_开头）
    if payment.out_trade_no.startswith('TEMP_'):
        logger.warning(f"Payment {payment_id} has temporary out_trade_no: {payment.out_trade_no}")
        return JsonResponse({
            'success': False,
            'status': payment.status,
            'message': '支付订单未正确创建，请重新尝试'
        })
    
    # 如果支付已经成功，直接返回成功状态
    if payment.status == 'success':
        return JsonResponse({
            'success': True,
            'status': 'success',
            'message': '支付成功'
        })
    
    # 调用Z-Pay查询支付状态
    logger.info(f"Calling zpay_service.query_payment_status with out_trade_no: {payment.out_trade_no}")
    try:
        result = zpay_service.query_payment_status(out_trade_no=payment.out_trade_no)
        logger.info(f"Z-Pay query result: {result}")
        
        if result['success'] and result['trade_status'] == 'TRADE_SUCCESS':
            # 更新支付状态
            payment.status = 'success'
            payment.alipay_trade_no = result['trade_no']  # 保持字段名一致
            payment.paid_at = timezone.now()
            payment.save()
            
            logger.info(f"Payment {payment.id} updated to success")
            
            # 更新报名状态（如果需要）
            registration = payment.registration
            registration.is_paid = True
            registration.save()
            
            return JsonResponse({
                'success': True,
                'status': 'success',
                'message': '支付成功'
            })
        else:
            logger.info(f"Payment {payment.id} not successful. Message: {result.get('message', 'Payment not completed')}")
            return JsonResponse({
                'success': False,
                'status': payment.status,
                'message': result.get('message', '支付未完成')
            })
    except Exception as e:
        logger.error(f"Failed to query payment status: {e}")
        return JsonResponse({
            'success': False,
            'status': payment.status,
            'message': '查询支付状态时发生错误'
        })


@csrf_exempt
@require_POST
def zpay_notify(request):
    """
    Z-Pay异步通知处理
    """
    logger.info("Received Z-Pay notification")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request body: {request.body}")
    logger.info(f"Request GET: {request.GET}")
    logger.info(f"Request POST: {request.POST}")
    
    try:
        # 获取通知数据
        data = request.POST.dict() if request.method == 'POST' else request.GET.dict()
        
        if not data:
            logger.warning("Received empty notification data")
            return HttpResponse("fail")
        
        # 验证签名
        if not zpay_service.verify_notification(data):
            logger.warning("Z-Pay notification signature verification failed")
            return HttpResponse("fail")
        
        # 获取商户订单号
        out_trade_no = data.get('out_trade_no')
        if not out_trade_no:
            logger.warning("Missing out_trade_no in notification")
            return HttpResponse("fail")
        
        # 获取支付状态
        trade_status = data.get('trade_status')
        if trade_status != 'TRADE_SUCCESS':
            logger.info(f"Trade status is not success: {trade_status}")
            return HttpResponse("success")
        
        # 查找对应的支付记录
        try:
            payment = Payment.objects.get(out_trade_no=out_trade_no)
        except Payment.DoesNotExist:
            logger.warning(f"Payment record not found for out_trade_no: {out_trade_no}")
            return HttpResponse("fail")
        
        # 更新支付状态
        if payment.status != 'success':
            payment.status = 'success'
            payment.alipay_trade_no = data.get('trade_no', '')  # 保持字段名一致
            payment.paid_at = timezone.now()
            payment.save()
            
            # 更新报名状态
            registration = payment.registration
            registration.is_paid = True
            registration.save()
            
            logger.info(f"Payment {payment.id} updated to success via notification")
        
        return HttpResponse("success")
        
    except Exception as e:
        logger.error(f"Error processing Z-Pay notification: {e}")
        return HttpResponse("fail")


@login_required
def initiate_refund(request, refund_request_id):
    """
    发起退款（目前仅记录退款申请，需要手动处理）
    """
    refund_request = get_object_or_404(RefundRequest, id=refund_request_id, 
                                     registration__user=request.user)
    
    # 检查是否已存在退款记录
    if hasattr(refund_request, 'refund'):
        messages.info(request, '该退款申请已处理')
        return redirect('event:my_events')
    
    try:
        with transaction.atomic():
            # 创建退款记录
            refund = refund_request.refund_set.create(
                amount=refund_request.registration.payment.amount,
                status='pending',
                out_refund_no=zpay_service._generate_out_trade_no()
            )
            
            # 更新退款申请状态
            refund_request.status = 'processing'
            refund_request.processed_at = timezone.now()
            refund_request.save()
            
        messages.success(request, '退款申请已提交，我们会尽快处理')
        
    except Exception as e:
        logger.error(f"Failed to initiate refund: {e}")
        messages.error(request, '退款申请提交失败，请稍后重试')
    
    return redirect('event:my_events')


def test_payment_page(request):
    """测试支付页面"""
    return render(request, 'pay/test_payment.html')


def test_payment(request):
    """测试支付功能"""
    if request.method == 'POST':
        amount = request.POST.get('amount', '0.01')
        subject = request.POST.get('subject', '测试支付')
        
        try:
            # 创建测试支付
            result = zpay_service.create_payment(
                amount=amount,
                subject=subject,
                registration_id=1  # 测试用ID
            )
            
            if result['success']:
                # 重定向到支付页面
                return redirect(result['pay_url'])
            else:
                messages.error(request, f"创建支付失败: {result['message']}")
        except Exception as e:
            messages.error(request, f"创建支付时发生错误: {str(e)}")
    
    return render(request, 'pay/test_payment.html')