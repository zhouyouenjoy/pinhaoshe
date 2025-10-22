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

    # 检查是否已存在待支付的订单
    pending_payment = Payment.objects.filter(
        registration=registration,
        status='pending'
    ).first()
    
    if pending_payment and pending_payment.out_trade_no:
        # 如果存在待支付订单且有订单号，则复用该订单号
        logger.info(f"Reusing existing payment order: {pending_payment.out_trade_no}")
        
        # 根据支付方式选择支付类型
        payment_method_map = {
            'alipay': 'alipay',
            'wxpay': 'wxpay',
            'qqpay': 'qqpay',
            'tenpay': 'tenpay',
        }
        pay_type = payment_method_map.get(pending_payment.payment_method, 'wxpay')
        
        try:
            result = zpay_service.create_payment(
                amount=registration.session.model.fee,
                subject=f"活动报名费 - {registration.session.model.event.title}",
                registration_id=registration.id,
                pay_type=pay_type,
                out_trade_no=pending_payment.out_trade_no  # 复用现有订单号
            )
            
            logger.info(f"Z-Pay create payment result with reused order: {result}")
            
            if result['success']:
                # 更新支付记录状态
                pending_payment.status = 'pending'
                pending_payment.save()
                
                logger.info(f"Reused payment order with out_trade_no: {pending_payment.out_trade_no}")
                
                # 重定向到Z-Pay支付页面
                return redirect(result['pay_url'])
            else:
                messages.error(request, f"创建支付订单失败: {result['message']}")
                return redirect('event:event_detail', pk=registration.session.model.event.id)
                
        except Exception as e:
            logger.error(f"Failed to reuse payment for registration {registration_id}: {e}")
            messages.error(request, '创建支付订单时发生错误，请稍后重试')
            return redirect('event:event_detail', pk=registration.session.model.event.id)
    else:
        # 生成临时订单号（仅用于日志）
        temp_out_trade_no = zpay_service._generate_out_trade_no()

        # 调用Z-Pay创建支付订单
        subject = f"活动报名费 - {registration.session.model.event.title}"
        logger.info(f"Calling zpay_service.create_payment with amount: {registration.session.model.fee}, subject: {subject}")
        
        # 根据支付方式选择支付类型
        payment_method_map = {
            'alipay': 'alipay',
            'wxpay': 'wxpay',
            'qqpay': 'qqpay',
            'tenpay': 'tenpay',
        }
        pay_type = payment_method_map.get(existing_payment.payment_method if existing_payment else 'wxpay', 'wxpay')
        
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
                        'payment_method': existing_payment.payment_method if existing_payment else 'wxpay',
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


def payment_success_callback(request):
    """
    处理支付平台的回调请求
    """
    # 从GET参数中获取out_trade_no
    out_trade_no = request.GET.get('out_trade_no')
    if not out_trade_no:
        return HttpResponse("Missing out_trade_no", status=400)
    
    try:
        payment = Payment.objects.get(out_trade_no=out_trade_no)
        
        # 主动查询Z-Pay API验证支付状态
        try:
            result = zpay_service.query_payment_status(out_trade_no=payment.out_trade_no)
            logger.info(f"Z-Pay query result in callback: {result}")
            
            if result['success'] and result['trade_status'] == 'TRADE_SUCCESS':
                # 更新支付状态
                payment.status = 'success'
                payment.trade_no = result['trade_no']
                payment.paid_at = timezone.now()
                payment.save()
                
                # 更新报名状态
                registration = payment.registration
                registration.is_paid = True
                registration.save()
                
                logger.info(f"Payment {payment.id} updated to success via API query")
            else:
                logger.warning(f"Payment {payment.id} verification failed: {result}")
                # 可以选择不更新状态，或者根据需要更新为失败状态
        except Exception as e:
            logger.error(f"Failed to query Z-Pay payment status: {e}")
            # 即使查询失败，也可以基于通知更新状态，但记录警告
            payment.status = 'pending'  # 保持待支付状态，需要进一步确认
            payment.save()
        
        # 重定向到支付成功页面
        return redirect('pay:payment_success', payment_id=payment.id)
    except Payment.DoesNotExist:
        logger.error(f"Payment not found for out_trade_no: {out_trade_no}")
        return HttpResponse("Payment not found", status=404)
    except Exception as e:
        logger.error(f"Error processing payment callback: {e}")
        return HttpResponse("Error processing payment", status=500)


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
            payment.trade_no = result['trade_no']  # 使用易支付订单号
            payment.paid_at = timezone.now()
            # 使用所有返回参数更新payment表
            payment.payment_method = result.get('type', payment.payment_method)  # 支付方式
            payment.amount = result.get('money', payment.amount)  # 支付金额
            payment.name = result.get('name', payment.name)  # 商品名称
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
#@require_POST
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
        if request.method == 'POST':
            data = request.POST.dict()
        else:
            data = request.GET.dict()
        
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
        
        # 首先检查对应业务数据的状态，判断该通知是否已经处理过
        if payment.status == 'success':
            logger.info(f"Payment {payment.id} already processed successfully, returning success")
            # 如果已经处理过，直接返回成功结果，避免重复处理
            return HttpResponse("success")
        
        # 使用数据库锁防止并发处理同一笔订单
        from django.db import transaction
        try:
            with transaction.atomic():
                # 重新获取支付记录并加锁
                payment = Payment.objects.select_for_update().get(out_trade_no=out_trade_no)
                
                # 再次检查状态，确保在获取锁之后没有被其他进程处理
                if payment.status == 'success':
                    logger.info(f"Payment {payment.id} already processed successfully after lock, returning success")
                    return HttpResponse("success")
                
                # 验证订单金额是否与商户侧的订单金额一致
                if not zpay_service.verify_amount(data, payment.amount):
                    logger.warning(f"Payment amount verification failed for payment {payment.id}")
                    return HttpResponse("fail")
                
                # 主动查询Z-Pay API验证支付状态，确保支付确实成功
                try:
                    query_result = zpay_service.query_payment_status(out_trade_no=payment.out_trade_no)
                    logger.info(f"Z-Pay query result in notification: {query_result}")
                    
                    if not (query_result['success'] and query_result['trade_status'] == 'TRADE_SUCCESS'):
                        logger.warning(f"Payment verification failed via API query: {query_result}")
                        # API查询结果与通知不一致，记录警告但继续处理
                        # 不返回，继续使用通知数据更新状态
                except Exception as e:
                    logger.error(f"Failed to query Z-Pay payment status for verification: {e}")
                    # 即使查询失败，也基于通知处理，但记录警告
                
                # 更新支付状态
                payment.status = 'success'
                payment.trade_no = data.get('trade_no', data.get('transaction_id', ''))  # 更新为trade_no字段
                payment.paid_at = data.get('endtime', timezone.now())  # 使用支付完成时间
                # 使用所有可用参数更新payment表
                if 'type' in data:
                    payment.payment_method = data['type']  # 支付方式
                if 'money' in data:
                    payment.amount = data['money']  # 支付金额
                if 'name' in data:
                    payment.name = data['name']  # 商品名称
                if 'buyer' in data:
                    payment.buyer = data['buyer']  # 支付者账号
                payment.save()
                
                # 更新报名状态
                registration = payment.registration
                registration.is_paid = True
                registration.save()
                
                logger.info(f"Payment {payment.id} updated to success via notification")
        except Exception as e:
            logger.error(f"Error processing payment with lock: {e}")
            raise e
        
        # 成功处理后返回success
        return HttpResponse("success")
        
    except Exception as e:
        logger.error(f"Error processing Z-Pay notification: {e}")
        # 发生异常时返回fail，让Z-Pay平台按策略重新发起通知
        return HttpResponse("fail")


@login_required
def initiate_refund(request, refund_request_id):
    """
    发起退款（通过Z-Pay API处理）
    """
    print(f"Initiating refund for refund_request_id: {refund_request_id}")
    refund_request = get_object_or_404(RefundRequest, id=refund_request_id, 
                                     registration__user=request.user)
    
    # 检查是否已存在退款记录
    if hasattr(refund_request, 'refund_record'):
        messages.info(request, '该退款申请已处理')
        return redirect('event:my_events')
    
    try:
        with transaction.atomic():
            # 创建退款记录
            refund = refund_request.refund_record.create(
                amount=refund_request.registration.payment.amount,
                status='processing',
                out_refund_no=zpay_service._generate_out_trade_no()
            )
            
            # 更新退款申请状态
            refund_request.status = 'processing'
            refund_request.processed_at = timezone.now()
            refund_request.save()
            
        # 调用Z-Pay API发起退款
        payment = refund_request.registration.payment
        print(f"Initiating refund for payment: {payment.out_trade_no}")
        print(f"Payment details - trade_no: {payment.trade_no}, out_trade_no: {payment.out_trade_no}, amount: {payment.amount}")
        logger.info(f"Initiating refund for payment: {payment.out_trade_no}")
        logger.info(f"Payment details - trade_no: {payment.trade_no}, out_trade_no: {payment.out_trade_no}, amount: {payment.amount}")
        
        result = zpay_service.refund(
            trade_no=payment.trade_no,
            out_trade_no=payment.out_trade_no,
            money=payment.amount
        )
        
        logger.info(f"Refund result: {result}")
        print(f"Refund result: {result}")
        
        if result['success']:
            # 退款成功，更新退款记录状态
            refund.status = 'success'
            refund.refunded_at = timezone.now()
            refund.save()
            
            # 更新退款申请状态
            refund_request.status = 'approved'
            refund_request.processed_at = timezone.now()
            refund_request.save()
            
            # 标记报名记录为已退款
            registration = refund_request.registration
            registration.is_refunded = True
            registration.save()
            
            print(f"Refund successful for refund_request_id: {refund_request_id}")
            messages.success(request, f'退款申请已成功处理: {result["message"]}')
        else:
            # 退款失败，更新退款记录状态
            refund.status = 'failed'
            refund.save()
            
            print(f"Refund failed for refund_request_id: {refund_request_id}")
            messages.error(request, f'退款申请处理失败: {result["message"]}')
            
    except Exception as e:
        logger.error(f"Failed to initiate refund: {e}")
        print(f"Failed to initiate refund: {e}")
        
        # 如果有退款记录，更新为失败状态
        if 'refund' in locals():
            refund.status = 'failed'
            refund.save()
        
        messages.error(request, '退款申请提交失败，请稍后重试')
    
    return redirect('event:my_events')
