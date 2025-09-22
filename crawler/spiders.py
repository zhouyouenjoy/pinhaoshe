"""
爬虫工具模块，用于从抖音、小红书、B站爬取照片数据
"""

import time
import os
import sys
import os.path
import tempfile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from django.utils import timezone

# 延迟导入Django模型，避免循环导入
def get_crawled_models():
    from crawler.models import CrawledUser, CrawledPost, CrawledMedia
    return CrawledUser, CrawledPost, CrawledMedia


class BaseSpider:
    """
    爬虫基类，定义通用方法和属性
    """
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        # 创建一个持久的用户数据目录
        self.user_data_dir = os.path.join(tempfile.gettempdir(), 'selenium_chrome_profile')
        os.makedirs(self.user_data_dir, exist_ok=True)
        # 注意：不再在此处调用 self.init_driver()，由子类决定何时以及如何初始化
        
    def init_driver(self, start_url=None):
        """
        初始化WebDriver
        
        Args:
            start_url: 启动浏览器后打开的初始URL
        """
        chrome_options = Options()
        # 核心：禁用GCM服务
        chrome_options.add_argument("--disable-gcm")
        # 辅助：屏蔽不必要的日志输出
        chrome_options.add_argument("--log-level=3")  # 只显示严重错误
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 排除日志开关
        chrome_options.add_argument("--window-size=1920,1080")
        # 添加用户数据目录以保持登录状态
        chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        
        # 添加保持登录状态的相关选项
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-plugins-discovery")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # 根据headless参数决定是否显示浏览器窗口
        if self.headless:
            chrome_options.add_argument("--headless")
        
        try:
            # 使用webdriver-manager自动下载和管理ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("成功连接到Chrome浏览器")
            
            # 打开初始URL（如果提供了URL）
            if start_url:
                self.driver.get(start_url)
                print(f"已打开网址: {start_url}")
        except Exception as e:
            print(f"无法连接到Chrome浏览器: {e}")
        
    def close_driver(self):
        """
        关闭WebDriver
        """
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException as e:
                print(f"关闭WebDriver时发生异常: {e}")
            finally:
                self.driver = None
            # 无论如何，都将driver设为None
        self.driver = None
        
    def scroll_to_bottom(self, pause_time=2):
        """
        滚动到页面底部，用于加载更多内容
        """
        # 获取滚动前的高度
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # 滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 等待新内容加载
            time.sleep(pause_time)
            
            # 计算新的滚动高度
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def get_images_by_class(self, css_selector):
        """
        根据CSS选择器查找元素并提取图片URL
        
        Args:
            css_selector: CSS选择器字符串
            这个可恶的css选择器不能有空格 要用 . 替换。
        Returns:
            list: 图片URL列表
        """
        print(f"开始执行get_images_by_class方法，CSS选择器: {css_selector}")  # 添加调试日志
        
        image_urls = []
        css_selector = f".{css_selector.replace(' ', '.')}"
        try:
            # 等待元素加载完成
            wait = WebDriverWait(self.driver, 10)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
                print(f"元素已加载完成: {css_selector}")
            except:
                print(f"元素可能需要更多时间加载: {css_selector}")
            
            # 查找所有具有指定class的元素
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            print(f"找到 {len(elements)} 个具有class='{css_selector}'的元素")
            
            # 如果没有找到，尝试其他方式
            if len(elements) == 0:
                # 尝试使用XPath
                # 将CSS类名转换为XPath表达式
                classes = css_selector.strip('.').split('.')
                if len(classes) >= 2:
                    xpath = f"//*[contains(@class, '{classes[0]}') and contains(@class, '{classes[1]}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    print(f"使用XPath找到 {len(elements)} 个元素")
            
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
                                    from urllib.parse import urljoin
                                    current_url = self.driver.current_url
                                    img_url = urljoin(current_url, img_url)
                                
                                print(f"  图片 {j+1}: {img_url}")
                                
                                # 添加到结果列表
                                if img_url not in image_urls:
                                    image_urls.append(img_url)
                            else:
                                print(f"  未找到图片链接")
                        except Exception as e:
                            print(f"  处理图片时出错: {str(e)}")
                except Exception as e:
                    print(f"处理元素 {i} 时出错: {str(e)}")
        
        except Exception as e:
            print(f"查找元素时出错: {str(e)}")
        
        print(f"图片URL提取完成，共找到 {len(image_urls)} 个唯一图片URL")
        return image_urls

    def get_captions_by_class(self, css_selector):
        """
        根据CSS选择器查找元素并提取文案内容（纯文本）
        
        Args:
            css_selector: CSS选择器字符串，例如"arnSiSbK hT34TYMB ONzzdL2F"
            
        Returns:
            list: 文案内容列表
        """
        print(f"开始执行get_captions_by_class方法，CSS选择器: {css_selector}")
        
        captions = []
        # 处理包含空格的CSS类名，将其转换为正确的CSS选择器格式
        css_selector = f".{css_selector.replace(' ', '.')}"
        
        try:
            # 等待元素加载完成
            wait = WebDriverWait(self.driver, 10)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
                print(f"元素已加载完成: {css_selector}")
            except:
                print(f"元素可能需要更多时间加载: {css_selector}")
            
            # 查找所有具有指定class的元素
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            print(f"找到 {len(elements)} 个具有class='{css_selector}'的元素")
            
            # 如果没有找到，尝试使用XPath
            if len(elements) == 0:
                # 将CSS类名转换为XPath表达式
                classes = css_selector.strip('.').split('.')
                if len(classes) >= 2:
                    xpath = f"//*[contains(@class, '{classes[0]}') and contains(@class, '{classes[1]}')]"
                    if len(classes) >= 3:
                        xpath = f"//*[contains(@class, '{classes[0]}') and contains(@class, '{classes[1]}') and contains(@class, '{classes[2]}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    print(f"使用XPath找到 {len(elements)} 个元素")
            
            # 遍历每个元素，提取其中的文本内容
            for i, element in enumerate(elements):
                try:
                    # 获取元素的文本内容
                    caption_text = element.text.strip()
                    print(f"处理元素 {i+1}/{len(elements)}: {caption_text[:50]}{'...' if len(caption_text) > 50 else ''}")
                    
                    # 只添加非空文本
                    if caption_text:
                        captions.append(caption_text)
                    else:
                        print(f"  元素 {i+1} 的文本内容为空")
                except Exception as e:
                    print(f"处理元素 {i} 时出错: {str(e)}")
        
        except Exception as e:
            print(f"查找元素时出错: {str(e)}")
        
        print(f"文案提取完成，共找到 {len(captions)} 条文案")
        return captions

    def get_user_avatar_by_class(self, css_selector):
        """
        根据CSS选择器查找用户头像URL
        
        Args:
            css_selector: CSS选择器字符串，例如"B0JKdzQ8 KsoclCZj sVGJfEdt"
            
        Returns:
            str: 用户头像URL，如果未找到则返回None
        """
        print(f"开始执行get_user_avatar_by_class方法，CSS选择器: {css_selector}")
        
        # 处理包含空格的CSS类名
        css_selector = f".{css_selector.replace(' ', '.')}"
        
        try:
            # 等待元素加载完成
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
            
            # 查找具有指定class的元素
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            print(f"找到 {len(elements)} 个具有class='{css_selector}'的元素")
            
            # 遍历每个元素，查找其中的图片
            for element in elements:
                try:
                    # 查找元素中的图片标签
                    img_tags = element.find_elements(By.TAG_NAME, "img")
                    for img_tag in img_tags:
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
                                from urllib.parse import urljoin
                                current_url = self.driver.current_url
                                img_url = urljoin(current_url, img_url)
                            
                            print(f"找到用户头像: {img_url}")
                            return img_url
                except Exception as e:
                    print(f"处理元素时出错: {str(e)}")
        except Exception as e:
            print(f"查找用户头像时出错: {str(e)}")
        
        print("未找到用户头像")
        return None

    def get_username_by_class(self, css_selector):
        """
        根据CSS选择器查找用户名
        
        Args:
            css_selector: CSS选择器字符串，例如"account-name userAccountTextHover"
            
        Returns:
            str: 用户名，如果未找到则返回None
        """
        print(f"开始执行get_username_by_class方法，CSS选择器: {css_selector}")
        
        # 处理包含空格的CSS类名
        css_selector = f".{css_selector.replace(' ', '.')}"
        
        try:
            # 等待元素加载完成
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
            
            # 查找具有指定class的元素
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            print(f"找到 {len(elements)} 个具有class='{css_selector}'的元素")
            
            # 遍历每个元素，提取其中的文本内容
            for element in elements:
                try:
                    # 获取元素的文本内容
                    username_text = element.text.strip()
                    if username_text:
                        # 去掉最开头的@符号
                        if username_text.startswith('@'):
                            username_text = username_text[1:]
                        print(f"找到用户名: {username_text}")
                        return username_text
                except Exception as e:
                    print(f"处理元素时出错: {str(e)}")
        except Exception as e:
            print(f"查找用户名时出错: {str(e)}")
        
        print("未找到用户名")
        return None

    def get_images_from_container(self, container_css_selector):
        """
        定位轮播图容器并提取其中的照片
        
        Args:
            container_css_selector: 容器CSS选择器，例如"nM3w4mVK cmI2tyuz focusPanel"
            
        Returns:
            list: 图片URL列表，仅来自照片最多的那个容器
        """
        print(f"开始执行get_images_from_container方法，容器CSS选择器: {container_css_selector}")
        
        # 处理包含空格的CSS类名
        container_css_selector = f".{container_css_selector.replace(' ', '.')}"
        
        try:
            # 等待容器元素加载完成
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_css_selector)))
            
            # 查找所有具有指定class的容器元素
            containers = self.driver.find_elements(By.CSS_SELECTOR, container_css_selector)
            print(f"找到 {len(containers)} 个容器元素")
            
            max_images = 0
            target_container = None
            
            # 遍历每个容器，找到包含照片最多的那个
            for i, container in enumerate(containers):
                try:
                    # 在当前容器内查找所有图片标签
                    img_tags = container.find_elements(By.TAG_NAME, "img")
                    print(f"  容器 {i+1} 包含 {len(img_tags)} 个图片标签")
                    
                    # 更新包含最多图片的容器
                    if len(img_tags) > max_images:
                        max_images = len(img_tags)
                        target_container = container
                except Exception as e:
                    print(f"处理容器 {i} 时出错: {str(e)}")
            
            # 如果找到了包含图片的容器
            if target_container and max_images > 0:
                print(f"选择包含 {max_images} 张图片的容器")
                image_urls = []
                
                # 提取该容器中的所有图片URL
                img_tags = target_container.find_elements(By.TAG_NAME, "img")
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
                                from urllib.parse import urljoin
                                current_url = self.driver.current_url
                                img_url = urljoin(current_url, img_url)
                            
                            print(f"  图片 {j+1}: {img_url}")
                            
                            # 添加到结果列表
                            if img_url not in image_urls:
                                image_urls.append(img_url)
                        else:
                            print(f"  未找到图片链接")
                    except Exception as e:
                        print(f"  处理图片时出错: {str(e)}")
                
                print(f"从目标容器提取完成，共找到 {len(image_urls)} 个唯一图片URL")
                return image_urls
            else:
                print("未找到包含图片的容器")
                return []
                
        except Exception as e:
            print(f"查找容器时出错: {str(e)}")
            return []

class DouyinSpider(BaseSpider):
    """
    抖音爬虫
    """
    def __init__(self, headless=True):
        super().__init__(headless)
        super().init_driver("https://www.douyin.com/")
        self.platform = 'douyin'
        
    def crawl_user(self, user_url):
        """
        爬取用户信息
        """
        pass  # 待实现
        
    def crawl_photos(self, user_id):
        """
        爬取用户照片
        """
        pass  # 待实现


class XiaohongshuSpider(BaseSpider):
    """
    小红书爬虫
    """
    def __init__(self, headless=True):
        super().__init__(headless)
        super().init_driver("https://www.xiaohongshu.com/")
        self.platform = 'xiaohongshu'
        
    def crawl_user(self, user_url):
        """
        爬取用户信息
        """
        pass  # 待实现
        
    def crawl_photos(self, user_id):
        """
        爬取用户照片
        """
        pass  # 待实现


class BilibiliSpider(BaseSpider):
    """
    B站爬虫
    """
    def __init__(self, headless=True):
        super().__init__(headless)
        super().init_driver("https://www.bilibili.com/")
        self.platform = 'bilibili'
        
    def crawl_user(self, user_url):
        """
        爬取用户信息
        """
        pass  # 待实现
        
    def crawl_photos(self, user_id):
        """
        爬取用户照片
        """
        pass  # 待实现


def main():
    """
    主函数，用于运行爬虫
    """ 
    # 初始化爬虫，设置headless=False以显示浏览器窗口
    spider = DouyinSpider(headless=False)
    time.sleep(9.5)
    
    print(spider.driver.title)
    spider.get_images_by_class("wCekfc8o qxTcdFT5")
        
if __name__ == "__main__":
    main()