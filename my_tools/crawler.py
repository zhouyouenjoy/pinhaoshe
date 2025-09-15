import sys
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# 1. 配置选项，指定调试端口（与第一步命令中的端口一致，如9222）
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# 2. 初始化驱动（需确保ChromeDriver版本与测试版Chrome匹配）
# 若ChromeDriver已在系统环境变量中，可省略executable_path参数
driver = webdriver.Chrome(
    options=chrome_options,
)
title = driver.title

# 使用多种方式尝试正确显示中文

    # 方法1: 直接打印
print(f"当前测试版Chrome页面标题：{title}")

# 3. 测试连接（打印当前页面标题，验证是否成功）
# 后续可正常用driver操作（如爬取数据、模拟点击等）