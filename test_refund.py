#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')
django.setup()

from pay.services import zpay_service
from event.models import RefundRequest
from pay.models import Payment

def test_refund_functionality():
    """
    测试退款功能
    """
    print("=== Z-Pay退款功能测试 ===\n")
    
    # 测试1: 检查Z-Pay服务配置
    print("1. 检查Z-Pay服务配置:")
    print(f"   PID: {zpay_service.pid}")
    print(f"   API URL: {zpay_service.api_url}")
    print(f"   Refund URL: {zpay_service.refund_url}")
    print(f"   Notify URL: {zpay_service.notify_url}")
    print(f"   Return URL: {zpay_service.return_url}")
    print(f"   Site Name: {zpay_service.sitename}")
    print()
    
    # 测试2: 检查是否存在退款请求
    print("2. 检查数据库中的退款请求:")
    refund_requests = RefundRequest.objects.filter(status='approved').select_related(
        'registration__payment'
    )
    
    if refund_requests.exists():
        print(f"   找到 {refund_requests.count()} 个已批准的退款请求")
        refund_request = refund_requests.first()
        payment = refund_request.registration.payment
        print(f"   退款请求ID: {refund_request.id}")
        print(f"   关联支付ID: {payment.id}")
        print(f"   支付金额: {payment.amount}")
        print(f"   商户订单号: {payment.out_trade_no}")
        print(f"   交易号: {payment.trade_no}")
        print()
        
        # 测试3: 尝试发起退款
        print("3. 尝试发起退款:")
        try:
            print(f"   发起退款请求:")
            print(f"   - 交易号: {payment.trade_no}")
            print(f"   - 商户订单号: {payment.out_trade_no}")
            print(f"   - 退款金额: {payment.amount}")
            
            result = zpay_service.refund(
                trade_no=payment.trade_no,
                out_trade_no=payment.out_trade_no,
                money=payment.amount
            )
            
            print(f"   退款结果:")
            print(f"   - 成功: {result['success']}")
            if result['success']:
                print(f"   - 退款单号: {result.get('refund_no', 'N/A')}")
                print(f"   - 退款金额: {result.get('refund_money', 'N/A')}")
            print(f"   - 消息: {result['message']}")
            
        except Exception as e:
            print(f"   退款请求失败: {str(e)}")
    else:
        print("   数据库中没有已批准的退款请求")
        print()
        
        # 测试指定的订单号
        print("3. 使用指定订单号测试退款:")
        trade_no = "4200002885202510225287857105"
        out_trade_no = input("   商户订单号 (out_trade_no): ").strip()
        money = input("   退款金额 (money): ").strip()
        
        if trade_no:
            try:
                money = float(money) if money else 0
                print(f"   发起退款请求:")
                print(f"   - 交易号: {trade_no}")
                print(f"   - 商户订单号: {out_trade_no or 'N/A'}")
                print(f"   - 退款金额: {money}")
                
                result = zpay_service.refund(
                    trade_no=trade_no,
                    out_trade_no=out_trade_no if out_trade_no else None,
                    money=money
                )
                
                print(f"   退款结果:")
                print(f"   - 成功: {result['success']}")
                if result['success']:
                    print(f"   - 退款单号: {result.get('refund_no', 'N/A')}")
                    print(f"   - 退款金额: {result.get('refund_money', 'N/A')}")
                print(f"   - 消息: {result['message']}")
                
            except Exception as e:
                print(f"   退款请求失败: {str(e)}")
        else:
            print("   未提供有效的订单号，跳过退款测试")

if __name__ == "__main__":
    test_refund_functionality()