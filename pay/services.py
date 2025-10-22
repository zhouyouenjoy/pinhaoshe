import uuid
import logging
import requests
import hashlib
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import os
from decimal import Decimal

logger = logging.getLogger(__name__)


class ZPayService:
    """
    Z-Pay支付服务类
    处理Z-Pay订单码支付相关接口调用
    """
    
    def __init__(self):
        """
        初始化Z-Pay服务
        """
        self.pid = getattr(settings, 'ZPAY_PID', '')
        self.key = getattr(settings, 'ZPAY_KEY', '')
        self.notify_url = getattr(settings, 'ZPAY_NOTIFY_URL', '')
        self.return_url = getattr(settings, 'ZPAY_RETURN_URL', '')
        self.sitename = getattr(settings, 'ZPAY_SITENAME', 'Photo Gallery')
        
        # Z-Pay API 地址
        self.submit_url = 'https://z-pay.cn/submit.php'
        self.api_url = 'https://z-pay.cn/api.php'
        self.refund_url = 'https://zpayz.cn/api.php'  # 退款API地址
    
    def _generate_out_trade_no(self):
        """
        生成商户订单号
        改进：使用时间戳 + 随机字母数字组合，提高可读性和性能
        """
        import random
        import string
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        # 生成6位随机字母数字
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{timestamp}{random_part}"
    
    def _generate_sign(self, params):
        """
        生成签名
        
        Args:
            params (dict): 参数字典
            
        Returns:
            str: 签名
        """
        # 按照参数名ASCII码从小到大排序
        sorted_params = sorted(params.items())
        
        # 拼接参数
        sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params if v])
        
        # 拼接密钥
        sign_str += self.key
        
        # MD5加密
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        return sign
    
    def create_payment(self, amount, subject, registration_id, pay_type=settings.ZPAY_PAYTYPE, out_trade_no=None):
        """
        创建支付订单
        
        Args:
            amount (Decimal): 支付金额
            subject (str): 订单标题
            registration_id (int): 报名记录ID
            pay_type (str): 支付方式，alipay:支付宝,wxpay:微信支付,qqpay:QQ钱包,tenpay:财付通
            out_trade_no (str, optional): 商户订单号，如果提供则复用该订单号
            
        Returns:
            dict: 包含支付链接和订单信息的字典
        """
        # 如果提供了订单号则复用，否则生成新的订单号
        if out_trade_no is None:
            out_trade_no = self._generate_out_trade_no()
        
        # 构造参数
        params = {
            'pid': self.pid,
            'type': pay_type,
            'out_trade_no': out_trade_no,
            'notify_url': self.notify_url,
            'return_url': self.return_url,
            'name': subject,
            'money': str(amount),
            'sitename': self.sitename,
        }
        
        # 生成签名
        sign = self._generate_sign(params)
        params['sign'] = sign
        params['sign_type'] = 'MD5'
        
        try:
            # 发起支付请求
            response = requests.get(self.submit_url, params=params, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'out_trade_no': out_trade_no,
                    'pay_url': response.url,
                    'message': '支付订单创建成功'
                }
            else:
                raise Exception(f'支付接口请求失败，状态码: {response.status_code}')
        except Exception as e:
            logger.error(f"Failed to create Z-Pay payment: {e}")
            raise e
    
    def query_payment_status(self, out_trade_no=None):
        """
        查询支付状态
        
        Args:
            out_trade_no (str): 商户订单号
            
        Returns:
            dict: 支付状态信息
        """
        try:
            # 构造参数
            params = {
                'act': 'order',
                'pid': self.pid,
                'key': self.key,
                'out_trade_no': out_trade_no,
            }
            
            # 发起查询请求
            response = requests.get(self.api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                # 解析返回的JSON数据
                import json
                result = response.json()
                
                # 检查API返回的code字段判断查询是否成功
                # 确保正确处理code值，无论是int还是string类型
                code_value = result.get('code')
                if code_value == 1 or code_value == "1":
                    # 查询成功，获取支付状态（status为"1"表示支付成功，"0"表示未支付）
                    # 确保正确处理status值，无论是int还是string类型
                    status_value = result.get('status', 0)
                    trade_success = (status_value == 1 or status_value == "1")
                    
                    return {
                        'success': trade_success,
                        'trade_status': 'TRADE_SUCCESS' if trade_success else 'WAIT_BUYER_PAY',
                        'status_text': '已支付' if trade_success else '待支付',
                        'trade_no': result.get('trade_no', ''),  # 易支付订单号
                        'out_trade_no': result.get('out_trade_no', ''),  # 商户订单号
                        'endtime': result.get('endtime', ''),  # 完成交易时间
                        'name': result.get('name', ''),  # 商品名称
                        'money': result.get('money', ''),  # 商品金额
                        'message': result.get('msg', '查询成功')
                    }
                else:
                    # API返回错误码，查询失败
                    error_code = result.get('code', '未知')
                    error_msg = result.get('msg', '未知错误')
                    raise Exception(f'查询失败 [错误码: {error_code}]: {error_msg}')
            else:
                raise Exception(f'查询接口请求失败，HTTP状态码: {response.status_code}')
        except Exception as e:
            logger.error(f"Failed to query Z-Pay payment status: {e}")
            raise e
    
    def verify_notification(self, data):
        """
        验证Z-Pay异步通知签名
        
        Args:
            data (dict): 通知数据
            
        Returns:
            bool: 签名是否有效
        """
        try:
            # 获取签名
            sign = data.pop('sign', None)
            sign_type = data.pop('sign_type', None)
            
            if not sign:
                return False
            
            # 生成签名进行比对
            expected_sign = self._generate_sign(data)
            
            return sign == expected_sign
        except Exception as e:
            logger.error(f"Failed to verify Z-Pay notification: {e}")
            return False

    def verify_amount(self, data, expected_amount):
        """
        验证通知中的订单金额是否与商户侧的订单金额一致
        
        Args:
            data (dict): 通知数据
            expected_amount (Decimal): 预期金额
            
        Returns:
            bool: 金额是否一致
        """
        try:
            # 从通知数据中获取金额
            notified_amount = data.get('money')
            if notified_amount is None:
                return False
                
            # 转换为Decimal进行比较
            from decimal import Decimal
            notified_amount = Decimal(str(notified_amount))
            
            # 比较金额是否一致
            return notified_amount == expected_amount
        except Exception as e:
            logger.error(f"Failed to verify amount: {e}")
            return False

    def refund(self, trade_no=None, out_trade_no=None, money=None):
        """
        发起退款申请
        
        Args:
            trade_no (str): 易支付订单号
            out_trade_no (str): 商户订单号
            money (Decimal): 退款金额
            
        Returns:
            dict: 退款结果
        """
        try:
            # 构造参数
            params = {
                'act': 'refund',
                'pid': self.pid,
                'key': self.key,
            }
            
            # 添加订单号参数（必须提供其中一个）
            if trade_no:
                params['trade_no'] = trade_no
            elif out_trade_no:
                params['out_trade_no'] = out_trade_no
            else:
                raise Exception('必须提供trade_no或out_trade_no中的一个')
            
            # 添加退款金额
            if money:
                params['money'] = str(money)
            else:
                raise Exception('退款金额不能为空')
            
            logger.info(f"Sending refund request to Z-Pay with params: {params}")
            print(f"Sending refund request to Z-Pay with params: {params}")
            
            # 发起退款请求
            response = requests.post(self.refund_url, data=params, timeout=30)
            
            logger.info(f"Received refund response from Z-Pay. Status code: {response.status_code}")
            print(f"Received refund response from Z-Pay. Status code: {response.status_code}")
            
            if response.status_code == 200:
                # 解析返回的JSON数据
                result = response.json()
                
                logger.info(f"Z-Pay refund API response: {result}")
                print(f"Z-Pay refund API response: {result}")
                
                # 检查API返回的code字段判断退款是否成功
                code_value = result.get('code')
                if code_value == 1 or code_value == "1":
                    refund_result = {
                        'success': True,
                        'refund_no': result.get('refund_no', ''),  # 退款单号
                        'refund_money': result.get('refund_money', ''),  # 退款金额
                        'message': result.get('msg', '退款成功')
                    }
                    print(f"Refund successful: {refund_result}")
                    return refund_result
                else:
                    # API返回错误码，退款失败
                    error_code = result.get('code', '未知')
                    error_msg = result.get('msg', '未知错误')
                    refund_result = {
                        'success': False,
                        'message': f'退款失败 [错误码: {error_code}]: {error_msg}'
                    }
                    print(f"Refund failed: {refund_result}")
                    return refund_result
            else:
                error_msg = f'退款接口请求失败，HTTP状态码: {response.status_code}'
                print(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Failed to refund via Z-Pay: {e}")
            print(f"Failed to refund via Z-Pay: {e}")
            raise e

# 全局Z-Pay服务实例
zpay_service = ZPayService()