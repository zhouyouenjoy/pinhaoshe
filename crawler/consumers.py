import json
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import importlib


class CrawlerConsumer(AsyncWebsocketConsumer):
    # 存储活跃的爬虫会话
    active_sessions = {}

    async def connect(self):
        await self.accept()
        print("WebSocket连接已建立")

    async def disconnect(self, close_code):
        # 清理所有与此连接相关的爬虫会话
        sessions_to_remove = []
        for session_id, session_data in self.active_sessions.items():
            if session_data['consumer'] == self:
                sessions_to_remove.append(session_id)
                # 关闭爬虫
                spider = session_data.get('spider')
                if spider:
                    await sync_to_async(spider.close_driver)()
        
        # 从活跃会话中移除
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        print("WebSocket连接已断开")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            print(f"收到WebSocket消息: {data}")  # 添加调试日志
            
            if message_type == 'start_crawl':
                await self.start_crawl(data)
            elif message_type == 'start_download':
                print(f"准备执行start_download方法: {data}")  # 添加调试日志
                await self.start_download(data)
            elif message_type == 'stop_crawl':
                await self.stop_crawl(data)
            else:
                await self.send_error('未知的消息类型')
        except json.JSONDecodeError:
            await self.send_error('无效的JSON格式')
        except Exception as e:
            await self.send_error(f'处理消息时出错: {str(e)}')

    async def start_crawl(self, data):
        """启动爬虫"""
        platform = data.get('platform')
        username = data.get('username')
        album_url = data.get('album_url')
        download_media = data.get('download_media')
        
        if not platform or not username:
            await self.send_error('平台和用户名是必需的')
            return
        
        # 创建会话ID
        session_id = str(uuid.uuid4())
        
        # 根据平台选择相应的爬虫类
        try:
            # 延迟导入爬虫模块，避免循环导入
            spiders_module = importlib.import_module('.spiders', package='crawler')
            
            if platform == 'douyin':
                spider = spiders_module.DouyinSpider(headless=False)
            elif platform == 'xiaohongshu':
                spider = spiders_module.XiaohongshuSpider(headless=False)
            elif platform == 'bilibili':
                spider = spiders_module.BilibiliSpider(headless=False)
            else:
                await self.send_error('不支持的平台')
                return
            
            # 存储会话信息
            self.active_sessions[session_id] = {
                'consumer': self,
                'spider': spider,
                'platform': platform,
                'username': username,
                'album_url': album_url,
                'download_media': download_media
            }
            
            # 发送成功消息
            await self.send(text_data=json.dumps({
                'type': 'crawl_started',
                'session_id': session_id,
                'message': f'已启动 {platform} 平台爬虫'
            }))
            
        except Exception as e:
            await self.send_error(f'启动爬虫失败: {str(e)}')

    async def start_download(self, data):
        """开始下载"""
        session_id = data.get('session_id')
        
        if not session_id or session_id not in self.active_sessions:
            await self.send_error('无效的会话ID')
            return
        
        session_data = self.active_sessions[session_id]
        spider = session_data['spider']
        
        try:
            # 让spider获取当前视窗
            current_url = await sync_to_async(lambda: spider.driver.current_url)()
            print(f"当前视窗URL: {current_url}")
            # 查找具有指定class的元素并获取图片URL
            # 使用CSS选择器查找class='wCekfc8o qxTcdFT5'的元素
            if session_data['platform'] == 'douyin':
                css_selector = ["wCekfc8o qxTcdFT5","arnSiSbK hT34TYMB ONzzdL2F"]
            elif session_data['platform'] == 'xiaohongshu':
                css_selector = "div.tiktok-1yjxlq-DivItemContainer"
            elif session_data['platform'] == 'bilibili':
                css_selector = "div.tiktok-1yjxlq-DivItemContainer"
    
            # 获取图片URL列表和文案内容
            image_urls = await sync_to_async(spider.get_images_by_class)(css_selector=css_selector[0])
            captions = []
            captions = await sync_to_async(spider.get_captions_by_class)(css_selector=css_selector[1])
            
            # 构造返回数据
            items = []
            for i, url in enumerate(image_urls[1:-1]):
                items.append({
                    'title': f'图片 {i+1}',
                    'url': url,
                })
            
            # 发送找到的图片数据和文案
            await self.send(text_data=json.dumps({
                'type': 'crawl_data',
                'items': items,
                'captions': captions
            }))
            
            # 模拟下载进度
            total_images = len(image_urls)
            if total_images > 0:
                for i in range(1, total_images + 1):
                    await asyncio.sleep(0.5)  # 模拟下载时间
                    progress = int((i / total_images) * 100)
                    await self.send(text_data=json.dumps({
                        'type': 'download_progress',
                        'progress': progress,
                        'message': f'正在下载... {progress}%'
                    }))
            
            # 下载完成
            await self.send(text_data=json.dumps({
                'type': 'download_complete',
                'message': f'下载完成，共下载 {total_images} 张图片'
            }))
            
        except Exception as e:
            print(f"下载过程中发生异常: {str(e)}")  # 添加调试日志
            # 发送错误消息，确保前端可以重新启用下载按钮
            await self.send_error(f'下载失败: {str(e)}')
            
    async def stop_crawl(self, data):
        """停止爬虫"""
        session_id = data.get('session_id')
        
        if not session_id or session_id not in self.active_sessions:
            await self.send_error('无效的会话ID')
            return
        
        session_data = self.active_sessions[session_id]
        spider = session_data.get('spider')
        
        try:
            # 关闭爬虫
            if spider:
                await sync_to_async(spider.close_driver)()
            # 从活跃会话中移除
            del self.active_sessions[session_id]
            
            # 发送停止确认消息
            await self.send(text_data=json.dumps({
                'type': 'crawl_stopped',
                'message': '爬虫已停止'
            }))
            
        except Exception as e:
            await self.send_error(f'停止爬虫失败: {str(e)}')

    async def send_error(self, message):
        """发送错误消息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))