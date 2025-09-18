"""
爬虫工具模块，用于从抖音、小红书、B站爬取照片数据
"""

import time
import os
import sys
import os.path
import tempfile

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up Django environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')
django.setup()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from django.utils import timezone
from crawler.models import CrawledUser, CrawledPost, CrawledMedia


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
        
    def init_driver(self, start_url="https://www.douyin.com/"):
        """
        初始化WebDriver
        
        Args:
            start_url: 启动浏览器后打开的初始URL，默认为百度
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
            
            # 打开初始URL
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
                # 首先尝试正常关闭
                self.driver.quit()
                print("浏览器已成功关闭")
            except Exception as e:
                print(f"关闭WebDriver时发生异常: {e}")
            finally:
                self.driver = None
        
        # 强制结束Chrome进程 - 更可靠的方法
        try:
            import psutil
            import os
            import time
            import subprocess
            
            # 等待一小段时间，让浏览器有机会自行关闭
            time.sleep(1)
            # 方法1: 使用psutil查找并终止所有Chrome进程
            chrome_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        chrome_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # 终止找到的Chrome进程
            for proc in chrome_processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                    # 进程可能已经终止或无法终止
                    pass
            
            # 方法2: 使用系统命令强制终止Chrome进程
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                                 capture_output=True, text=True)
                else:  # Unix/Linux/MacOS
                    subprocess.run(['pkill', '-f', 'chrome'], 
                                 capture_output=True, text=True)
            except Exception as e:
                print(f"使用系统命令终止Chrome进程时出错: {e}")
            
            print("浏览器进程清理完成")
        except Exception as e:
            print(f"无法强制结束Chrome进程: {e}，请手动关闭浏览器")
        
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
    spider.init_driver()
    
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