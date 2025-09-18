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
        
    def init_driver(self, start_url=None):
        """
        初始化WebDriver
        
        Args:
            start_url: 启动浏览器后打开的初始URL，默认为抖音
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


class DouyinSpider(BaseSpider):
    """
    抖音爬虫
    """
    def __init__(self, headless=True):
        super().__init__(headless)
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
    print("正在初始化爬虫...")
    spider.init_driver(start_url="https://www.douyin.com")
    
    # 检查驱动是否成功启动
    if not spider.driver:
        print("爬虫初始化失败，无法启动浏览器")
        return
    
    print("爬虫已启动，浏览器窗口应该已经打开")
    print("按Ctrl+C终止程序...")
    
    # 保持程序运行，直到手动关闭
    try:
        while True:
            # 尝试执行一个简单的WebDriver操作来检测浏览器是否存活
            try:
                _ = spider.driver.current_url
            except WebDriverException:
                print("\n检测到浏览器已关闭，正在执行清理...")
                spider.close_driver()
                print("爬虫已关闭")
                break # 退出循环
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n正在关闭爬虫...")
        spider.close_driver()
        print("爬虫已关闭")
        
if __name__ == "__main__":
    main()