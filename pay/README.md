# 支付应用 (Pay App)

该应用用于处理活动报名费的支付和退款功能，集成支付宝当面付（扫码支付）服务。

## 功能特性

1. **支付宝扫码支付**
   - 集成支付宝当面付API
   - 生成支付二维码
   - 实时查询支付状态

2. **退款处理**
   - 处理活动报名退款请求
   - 集成支付宝退款API
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
- `payment_method`: 支付方式 (支付宝扫码支付等)
- `alipay_trade_no`: 支付宝交易号
- `out_trade_no`: 商户订单号
- `qr_code`: 二维码内容
- `created_at`: 创建时间
- `paid_at`: 支付完成时间

### Refund (退款记录)
- `refund_request`: 关联的退款申请 (OneToOne)
- `amount`: 退款金额
- `status`: 退款状态 (待处理/退款中/退款成功/退款失败)
- `alipay_refund_no`: 支付宝退款交易号
- `out_refund_no`: 商户退款单号
- `created_at`: 创建时间
- `refunded_at`: 退款完成时间

## 接口说明

### 视图函数

1. `create_payment(registration_id)`: 创建支付订单
2. `payment_success(payment_id)`: 支付成功页面
3. `payment_status(payment_id)`: 查询支付状态 (AJAX)
4. `alipay_notify()`: 支付宝异步通知接口
5. `initiate_refund(refund_request_id)`: 发起退款

### URLs

- `pay:create_payment` - 创建支付订单
- `pay:payment_success` - 支付成功页面
- `pay:payment_status` - 查询支付状态
- `pay:alipay_notify` - 支付宝异步通知
- `pay:initiate_refund` - 发起退款

## 配置说明

在 `settings.py` 中添加以下配置：

```python
# 支付宝配置
ALIPAY_APP_ID = 'your_app_id'
ALIPAY_PRIVATE_KEY = 'your_private_key'
ALIPAY_PUBLIC_KEY = 'alipay_public_key'
ALIPAY_NOTIFY_URL = 'https://yourdomain.com/pay/alipay/notify/'
ALIPAY_RETURN_URL = 'https://yourdomain.com/pay/success/'
ALIPAY_SANDBOX = True  # 是否为沙箱环境
```

## 安装依赖

```bash
pip install python-alipay-sdk
```

## 使用流程

1. 用户报名活动后，系统创建支付订单
2. 用户扫描二维码完成支付
3. 系统接收到支付宝异步通知或用户手动查询更新支付状态
4. 支付成功后更新报名状态
5. 如需退款，管理员在后台审批退款申请
6. 系统调用支付宝退款接口处理退款

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

4. 配置URL路由

5. 实现视图逻辑

## 支付宝集成说明

本应用使用 [python-alipay-sdk](https://github.com/fzlee/alipay) 库与支付宝进行交互。

### 安装SDK
```bash
pip install python-alipay-sdk
```

### 配置说明

在生产环境中，需要在支付宝开放平台申请应用并获取以下信息：
1. APPID - 应用ID
2. 应用私钥 - 用于签名请求
3. 支付宝公钥 - 用于验签响应

### 沙箱环境测试

支付宝提供沙箱环境用于开发测试，可以在支付宝开放平台控制台获取沙箱账号进行测试。

## 注意事项

1. 支付宝异步通知URL必须是公网可访问的地址
2. 需要正确处理支付宝异步通知，防止重复处理
3. 在生产环境中，务必保护好私钥文件的安全
4. 建议记录所有与支付宝的交互日志，便于排查问题