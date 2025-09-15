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


def download_image(img_url, save_path, timeout=10):
    """下载图片并处理可能的异常"""
    try:
        # 添加超时设置，避免请求时间过长
        response = requests.get(img_url, timeout=timeout, stream=True)
        if response.status_code == 200:
            # 获取文件扩展名
            content_type = response.headers.get('content-type')
            extension = '.jpg'  # 默认扩展名
            if content_type:
                if 'png' in content_type:
                    extension = '.png'
                elif 'gif' in content_type:
                    extension = '.gif'
                elif 'webp' in content_type:
                    extension = '.webp'
            
            # 确保文件名正确
            if not save_path.endswith(extension):
                save_path = save_path.rsplit('.', 1)[0] + extension
            
            # 保存图片
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return True, save_path
        else:
            return False, f"状态码错误: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.ConnectionError:
        return False, "连接错误"
    except Exception as e:
        return False, str(e)


# 1. 配置选项，指定调试端口（与第一步命令中的端口一致，如9222）
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# 2. 初始化驱动（需确保ChromeDriver版本与测试版Chrome匹配）
# 若ChromeDriver已在系统环境变量中，可省略executable_path参数
driver = None
try:
    driver = webdriver.Chrome(options=chrome_options)
    print("成功连接到Chrome浏览器")
    
    # 3. 获取当前页面信息
    title = driver.title
    current_url = driver.current_url
    print(f"当前测试版Chrome页面标题：{title}")
    print(f"当前页面URL：{current_url}")

    # 4. 创建保存图片的目录
    save_dir = "downloaded_images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已创建图片保存目录：{save_dir}")

    # 5. 查找指定class的元素并下载图片
    target_class = "wCekfc8o qxTcdFT5"
    print(f"正在查找class='{target_class}'的元素...")

    # 尝试使用不同的方式查找元素
    try:
        pass  # 占位符，后续代码会继续添加逻辑，确保 try 语句有内容
        # 方式1: 使用CSS选择器
        css_selector = f".{target_class.replace(' ', '.')}"
        print(f"尝试使用CSS选择器: {css_selector}")
        
        # 等待元素加载完成
        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
            print("元素已加载完成")
        except:
            print("元素可能需要更多时间加载，继续尝试查找")
        
        # 查找所有具有指定class的元素
        elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
        print(f"找到 {len(elements)} 个具有class='{target_class}'的元素")
        
        # 如果没有找到，尝试其他方式
        if len(elements) == 0:
            print("未找到元素，尝试使用XPath")
            xpath = f"//*[contains(@class, '{target_class.split()[0]}') and contains(@class, '{target_class.split()[1]}')]"
            elements = driver.find_elements(By.XPATH, xpath)
            print(f"使用XPath找到 {len(elements)} 个元素")
        
        image_count = 0
        # 遍历每个元素，查找其中的图片
        for i, element in enumerate(elements):
            try:
                # 输出元素的部分信息，帮助调试
                element_text = element.text[:50] + "..." if len(element.text) > 50 else element.text
                print(f"处理元素 {i+1}/{len(elements)}: {element_text}")
                
                # 查找元素中的所有图片标签
                img_tags = element.find_elements(By.TAG_NAME, "img")
                print(f"  元素中包含 {len(img_tags)} 个图片标签")
                
                for j, img_tag in enumerate(img_tags):
                    try:
                        # 获取图片链接
                        img_url = img_tag.get_attribute("src")
                        if not img_url:
                            # 尝试获取其他可能的图片链接属性
                            img_url = img_tag.get_attribute("data-src") or img_tag.get_attribute("srcset")
                        
                        if img_url:
                            # 处理相对URL
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif img_url.startswith('/'):
                                from urllib.parse import urlparse
                                parsed_url = urlparse(current_url)
                                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                img_url = base_url + img_url
                            
                            print(f"  图片 {j+1}: {img_url}")
                            
                            # 生成图片文件名
                            img_name = f"image_{i}_{j}{int(time.time())}.jpg"
                            img_path = os.path.join(save_dir, img_name)
                            
                            # 下载图片
                            success, message = download_image(img_url, img_path)
                            if success:
                                image_count += 1
                                print(f"  已下载图片 {image_count}: {message}")
                            else:
                                print(f"  下载图片失败: {message}")
                        else:
                            print(f"  未找到图片链接")
                    except Exception as e:
                        print(f"  处理图片时出错: {str(e)}")
            except Exception as e:
                print(f"处理元素 {i} 时出错: {str(e)}")
        
        print(f"图片下载完成，共下载 {image_count} 张图片")
    except Exception as e:
        print(f"查找元素时出错: {str(e)}")
        print("可能的原因：")
        print("1. 当前页面中不存在class='wCekfc8o qxTcdFT5'的元素")
        print("2. 元素名称可能有误，请检查拼写")
        print("3. 页面可能需要登录或有反爬虫机制")
        print("4. 请确保Chrome浏览器已在调试模式下运行")
except Exception as e:
    print(f"连接浏览器时出错: {str(e)}")
    print("请确保Chrome浏览器已在调试模式下运行")
    print("启动命令示例: chrome.exe --remote-debugging-port=9222")

finally:
        # 6. 关闭浏览器驱动
        if driver:
            try:
                driver.quit()
                print("已关闭浏览器驱动")
            except:
                pass