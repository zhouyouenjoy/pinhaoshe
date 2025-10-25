#!/usr/bin/env python
import os
import sys
import django
import json
import requests
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
            
            # 构造请求参数用于显示
            params = {
                'act': 'refund',
                'pid': zpay_service.pid,
                'key': zpay_service.key,
                'trade_no': payment.trade_no,
                'money': str(payment.amount)
            }
            
            print(f"\n   请求URL: {zpay_service.refund_url}")
            print(f"   请求方法: POST")
            print(f"   Content-Type: application/json")
            print(f"   请求参数: {params}")
            
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
        print("   用户提供的交易号: 4200002885202510225287857105")
        trade_no = "4200002885202510225287857105"
        print(f"   使用交易号: {trade_no}")
        
        # 检查是否需要商户订单号
        use_out_trade_no = input("   是否需要提供商户订单号? (y/n): ").strip().lower()
        out_trade_no = ""
        if use_out_trade_no == 'y':
            out_trade_no = input("   商户订单号 (out_trade_no): ").strip()
        
        money = input("   退款金额 (money): ").strip()
        
        if trade_no or out_trade_no:
            try:
                money = float(money) if money else 0.01
                print(f"   发起退款请求:")
                print(f"   - 交易号: {trade_no or 'N/A'}")
                print(f"   - 商户订单号: {out_trade_no or 'N/A'}")
                print(f"   - 退款金额: {money}")
                
                # 构造请求参数用于显示
                params = {
                    'act': 'refund',
                    'pid': zpay_service.pid,
                    'key': zpay_service.key,
                    'money': str(money)
                }
                
                if trade_no:
                    params['trade_no'] = trade_no
                elif out_trade_no:
                    params['out_trade_no'] = out_trade_no
                
                print(f"\n   请求URL: {zpay_service.refund_url}")
                print(f"   请求方法: POST")
                print(f"   Content-Type: application/json")
                print(f"   请求参数: {params}")
                
                result = zpay_service.refund(
                    trade_no=trade_no if trade_no else None,
                    out_trade_no=out_trade_no if out_trade_no else None,
                    money=money
                )
                
                print(f"   退款结果:")
                print(f"   - 成功: {result['success']}")
                if result['success']:
                    print(f"   - 退款单号: {result.get('refund_no', 'N/A')}")
                    print(f"   - 退款金额: {result.get('refund_money', 'N/A')}")
                print(f"   - 消息: {result['message']}")
                
                # 显示完整的响应数据
                print(f"   - 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
            except Exception as e:
                print(f"   退款请求失败: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("   未提供有效的订单号，跳过退款测试")

import requests
import json

def test_refund_with_raw_request():
    print("=== Z-Pay退款API原始响应测试 ===\n")
    
    trade_no = "4200002868202510207875947126"
    out_trade_no = "20251020170222RPUAUP"
    money = input("   退款金额 (money): ").strip()
    
    if not money:
        money = "0.01"
    
    try:
        money = float(money)
        print(f"   发起退款请求:")
        print(f"   - 交易号: {trade_no}")
        print(f"   - 退款金额: {money}")
        
        # 构造表单参数（不含act，act放在URL中）
        params = {
            'pid': zpay_service.pid,  # 替换为实际pid
            'key': zpay_service.key,  # 替换为实际key
            'trade_no': trade_no,
            out_trade_no: out_trade_no,
            'money': str(money)
        }
        
        print(f"   请求参数: {params}")
        
        # 请求URL携带act=refund，与Java保持一致
        url = "https://zpayz.cn/api.php?act=refund"
        print(f"\n   请求URL: {url}")

        
        # 使用data参数发送表单格式（而非json）
        response = requests.post(
            url,
            data=params,  # 表单格式参数
            timeout=30
        )
        
        print(f"\n   HTTP响应:")
        print(f"   - 状态码: {response.status_code}")
        print(f"   - 响应头: {dict(response.headers)}")
        print(f"   - 响应内容: {response.text}")
        
        # 解析响应
        if response.status_code == 200 and response.text:
            try:
                result = response.json()
                print(f"\n   JSON解析结果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"   JSON解析失败: {e}")
        elif response.status_code == 200:
            print("   收到空响应")
        else:
            print(f"   请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"   请求过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    
    # 询问是否运行原始请求测试
    run_raw_test = input("\n是否运行原始请求测试? (y/n): ").strip().lower()
    if run_raw_test == 'y':
        test_refund_with_raw_request()