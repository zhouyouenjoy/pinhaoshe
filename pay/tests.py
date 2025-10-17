import unittest
from unittest.mock import patch, MagicMock
import hashlib
import requests
import os
import sys
import django
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')

# 如果Django尚未初始化，则进行初始化
try:
    django.setup()
except Exception:
    pass

# 发起支付请求
def pay(money, name, notify_url, out_trade_no, payType, pid, return_url, webName, key):
    # money = ''               # 金额
    # name = ''                # 商品名称
    # notify_url = ''          # 服务器异步通知地址
    # out_trade_no = ''        # 商户订单号
    # pid = ''                 # 商户ID
    # return_url = ''          # 页面跳转通知地址
    # webName = ''             # 网站名称
    # payType = ''             # 支付方式:alipay:支付宝,wxpay:微信支付,qqpay:QQ钱包,tenpay:财付通,
    # key = ''                 # 密钥,易支付注册会提供pid和秘钥

    # 对参数进行排序，生成待签名字符串--(具体看支付宝)
    sg = 'money=' + money + '&name=' + name + '&notify_url=' + notify_url +'&out_trade_no=' + out_trade_no + '&pid=' + pid + '&return_url=' + return_url + '&sitename=' + webName + '&type=' + payType
    # MD5加密--进行签名
    sign = hashlib.md5((sg+key).encode(encoding='UTF-8')).hexdigest()  # 签名计算
    # 最后要将参数返回给前端，前端访问url发起支付
    url = 'https://z-pay.cn/submit.php?' + sg + '&sign=' + sign + '&sign_type=MD5'

    res = requests.post(url).content.decode()
    return res

# 查询商户信息与结算规则
def act(pid, key):
    url = 'https://z-pay.cn/api.php?act=query&pid=' + pid + '&key=' + key
    res = requests.get(url).content.decode()
    return res

# 修改结算账号
def change(pid, key, account, username):
    url = 'https://z-pay.cn/api.php?act=change&pid=' + pid + '&key=' + key + '&account=' + account + '&username=' + username
    res = requests.get(url).content.decode()
    return res

# 查询结算记录
def settle(pid, key):
    url = 'https://z-pay.cn/api.php?act=settle&pid=' + pid + '&key=' + key
    res = requests.get(url).content.decode()
    return res

# 查询单个订单
def order(pid, key, out_trade_no):
    url = 'https://z-pay.cn/api.php?act=order&pid='+pid+'&key='+key+'&out_trade_no='+out_trade_no
    res = requests.get(url).content.decode()
    return res

# 批量查询订单
def orders(pid, key, limit):
    url = 'https://z-pay.cn/api.php?act=orders&pid=' + pid + '&key=' + key
    res = requests.get(url).content.decode()
    return res


class ZPayTestCase(unittest.TestCase):
    """测试Z-Pay支付功能"""

    def setUp(self):
        """测试前准备数据"""
        self.money = '0.01'              # 金额
        self.name = '测试商品'            # 商品名称
        self.notify_url = 'https://example.com/notify/'  # 服务器异步通知地址
        self.out_trade_no = 'TEST20251015001'  # 商户订单号
        self.payType = 'alipay'          # 支付方式:alipay:支付宝,wxpay:微信支付,qqpay:QQ钱包,tenpay:财付通
        self.pid = '123456'              # 商户ID
        self.return_url = 'https://example.com/return/'  # 页面跳转通知地址
        self.webName = '测试网站'         # 网站名称
        self.key = 'testkey123456'       # 密钥

    @patch('requests.post')
    def test_pay_function(self, mock_post):
        """测试支付功能"""
        # 模拟返回结果
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '<html><body>支付页面</body></html>'
        mock_post.return_value = mock_response

        # 调用支付函数
        result = pay(
            money=self.money,
            name=self.name,
            notify_url=self.notify_url,
            out_trade_no=self.out_trade_no,
            payType=self.payType,
            pid=self.pid,
            return_url=self.return_url,
            webName=self.webName,
            key=self.key
        )

        # 验证结果
        self.assertEqual(result, '<html><body>支付页面</body></html>')
        mock_post.assert_called_once()
        
        # 验证请求URL包含了必要的参数
        called_args = mock_post.call_args[0]
        url = called_args[0]
        self.assertIn('https://z-pay.cn/submit.php?', url)
        self.assertIn('money=' + self.money, url)
        self.assertIn('name=' + self.name, url)
        self.assertIn('notify_url=' + self.notify_url, url)
        self.assertIn('out_trade_no=' + self.out_trade_no, url)
        self.assertIn('pid=' + self.pid, url)
        self.assertIn('return_url=' + self.return_url, url)
        self.assertIn('sitename=' + self.webName, url)
        self.assertIn('type=' + self.payType, url)
        self.assertIn('sign=', url)
        self.assertIn('sign_type=MD5', url)

    @patch('requests.get')
    def test_act_function(self, mock_get):
        """测试查询商户信息功能"""
        # 模拟返回结果
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"code":1,"msg":"查询成功","data":{"pid":"123456"}}'
        mock_get.return_value = mock_response

        # 调用查询商户信息函数
        result = act(self.pid, self.key)

        # 验证结果
        self.assertEqual(result, '{"code":1,"msg":"查询成功","data":{"pid":"123456"}}')
        mock_get.assert_called_once_with(
            f'https://z-pay.cn/api.php?act=query&pid={self.pid}&key={self.key}'
        )

    @patch('requests.get')
    def test_change_account_function(self, mock_get):
        """测试修改结算账号功能"""
        account = 'test@example.com'
        username = '测试用户'
        
        # 模拟返回结果
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"code":1,"msg":"修改成功"}'
        mock_get.return_value = mock_response

        # 调用修改结算账号函数
        result = change(self.pid, self.key, account, username)

        # 验证结果
        self.assertEqual(result, '{"code":1,"msg":"修改成功"}')
        mock_get.assert_called_once_with(
            f'https://z-pay.cn/api.php?act=change&pid={self.pid}&key={self.key}&account={account}&username={username}'
        )

    @patch('requests.get')
    def test_settle_function(self, mock_get):
        """测试查询结算记录功能"""
        # 模拟返回结果
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"code":1,"msg":"查询成功","data":[]}'
        mock_get.return_value = mock_response

        # 调用查询结算记录函数
        result = settle(self.pid, self.key)

        # 验证结果
        self.assertEqual(result, '{"code":1,"msg":"查询成功","data":[]}')
        mock_get.assert_called_once_with(
            f'https://z-pay.cn/api.php?act=settle&pid={self.pid}&key={self.key}'
        )

    @patch('requests.get')
    def test_order_function(self, mock_get):
        """测试查询单个订单功能"""
        # 模拟返回结果
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"code":1,"msg":"查询成功","data":{"out_trade_no":"' + self.out_trade_no + '"}}'
        mock_get.return_value = mock_response

        # 调用查询单个订单函数
        result = order(self.pid, self.key, self.out_trade_no)

        # 验证结果
        self.assertEqual(result, '{"code":1,"msg":"查询成功","data":{"out_trade_no":"' + self.out_trade_no + '"}}')
        mock_get.assert_called_once_with(
            f'https://z-pay.cn/api.php?act=order&pid={self.pid}&key={self.key}&out_trade_no={self.out_trade_no}'
        )

    @patch('requests.get')
    def test_orders_function(self, mock_get):
        """测试批量查询订单功能"""
        limit = '50'
        
        # 模拟返回结果
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"code":1,"msg":"查询成功","data":[]}'
        mock_get.return_value = mock_response

        # 调用批量查询订单函数
        result = orders(self.pid, self.key, limit)

        # 验证结果
        self.assertEqual(result, '{"code":1,"msg":"查询成功","data":[]}')
        mock_get.assert_called_once_with(
            f'https://z-pay.cn/api.php?act=orders&pid={self.pid}&key={self.key}'
        )


if __name__ == '__main__':
    unittest.main()