import uuid
import logging
import requests
import hashlib
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import os

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
                
                if result.get('code') == 1:
                    # 状态码对应关系
                    status_mapping = {
                        '0': '待支付',
                        '1': '已支付',
                    }
                    
                    trade_status = result.get('data', {}).get('status', '0')
                    status_text = status_mapping.get(str(trade_status), '未知状态')
                    
                    return {
                        'success': trade_status == '1',
                        'trade_status': 'TRADE_SUCCESS' if trade_status == '1' else 'WAIT_BUYER_PAY',
                        'status_text': status_text,
                        'transaction_id': result.get('data', {}).get('trade_no', ''),
                        'message': '查询成功'
                    }
                else:
                    raise Exception(f'查询失败: {result.get("msg", "未知错误")}')
            else:
                raise Exception(f'查询接口请求失败，状态码: {response.status_code}')
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


# 全局Z-Pay服务实例
zpay_service = ZPayService()