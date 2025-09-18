import sys
import io
import os
import sys
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 1. 配置选项，指定调试端口（与第一步命令中的端口一致，如9222）
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# 2. 初始化驱动（需确保ChromeDriver版本与测试版Chrome匹配）
# 若ChromeDriver已在系统环境变量中，可省略executable_path参数
driver = None

try:
    driver = webdriver.Chrome(options=chrome_options)
    print("成功连接到Chrome浏览器")
except Exception as e:
    print(f"连接Chrome浏览器失败，请确保：")
    print(f"1. Chrome浏览器已通过命令行参数 --remote-debugging-port=9222 启动。")
    print(f"2. 端口 9222 未被占用。")
    print(f"3. ChromeDriver版本与Chrome浏览器版本兼容。")
    print(f"错误信息: {e}")
    sys.exit(1)

# 3. 获取当前页面信息
title = driver.title
current_url = driver.current_url
print(f"当前测试版Chrome页面标题：{title}")
print(f"当前页面URL：{current_url}")

    