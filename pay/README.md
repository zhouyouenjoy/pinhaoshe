# 支付应用 (Pay App)

该应用用于处理活动报名费的支付和退款功能，集成Z-Pay第三方支付服务。

## 功能特性

1. **Z-Pay第三方支付**
   - 集成Z-Pay支付API
   - 支持多种支付方式（支付宝、微信、QQ钱包等）
   - 生成支付链接和二维码
   - 实时查询支付状态

2. **退款处理**
   - 处理活动报名退款请求
   - 集成Z-Pay退款API
   - 跟踪退款状态

3. **订单管理**
   - 支付订单记录
   - 退款记录追踪
   - 支付状态同步

## 模型说明

### Payment (支付订单)
- `registration`: 关联的活动报名记录 (OneToOne)
- `amount`: 支付金额
- `status`: 支付状态 (待支付/支付成功/支付失败/已关闭)
- `payment_method`: 支付方式 (Z-Pay支付宝、微信支付等)
- `alipay_trade_no`: 交易号
- `out_trade_no`: 商户订单号
- `qr_code`: 二维码内容
- `created_at`: 创建时间
- `paid_at`: 支付完成时间

### Refund (退款记录)
- `refund_request`: 关联的退款申请 (OneToOne)
- `amount`: 退款金额
- `status`: 退款状态 (待处理/退款中/退款成功/退款失败)
- `alipay_refund_no`: 退款交易号
- `out_refund_no`: 商户退款单号
- `created_at`: 创建时间
- `refunded_at`: 退款完成时间

## 接口说明

### 视图函数

1. `create_payment(registration_id)`: 创建支付订单
2. `payment_success(payment_id)`: 支付成功页面
3. `payment_status(payment_id)`: 查询支付状态 (AJAX)
4. `zpay_notify()`: Z-Pay异步通知接口
5. `initiate_refund(refund_request_id)`: 发起退款

### URLs

- `pay:create_payment` - 创建支付订单
- `pay:payment_success` - 支付成功页面
- `pay:payment_status` - 查询支付状态
- `pay:zpay_notify` - Z-Pay异步通知
- `pay:initiate_refund` - 发起退款

## 配置说明

在 `settings.py` 中添加以下配置：

```python
# Z-Pay配置
ZPAY_PID = 'your_pid'
ZPAY_KEY = 'your_key'
ZPAY_NOTIFY_URL = 'https://yourdomain.com/pay/zpay/notify/'
ZPAY_RETURN_URL = 'https://yourdomain.com/pay/success/'
ZPAY_SANDBOX = True  # 是否为沙箱环境
```

## 使用流程

1. 用户报名活动后，系统创建支付订单
2. 用户通过支付链接或扫描二维码完成支付
3. 系统接收到Z-Pay异步通知或用户手动查询更新支付状态
4. 支付成功后更新报名状态
5. 如需退款，管理员在后台审批退款申请
6. 系统调用Z-Pay退款接口处理退款

## 开发和测试

1. 创建支付应用：
   ```bash
   python manage.py startapp pay
   ```

2. 添加应用到 `INSTALLED_APPS`:
   ```python
   INSTALLED_APPS = [
       ...
       'pay.apps.PayConfig',
   ]
   ```

3. 创建模型并迁移数据库：
   ```bash
   python manage.py makemigrations pay
   python manage.py migrate pay
   ```