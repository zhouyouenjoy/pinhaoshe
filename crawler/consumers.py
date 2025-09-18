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
            
            if message_type == 'start_crawl':
                await self.start_crawl(data)
            elif message_type == 'start_download':
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
            
            # 初始化爬虫
            await sync_to_async(spider.init_driver)()
            
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
            # 这里应该实现实际的下载逻辑
            # 目前只是模拟返回一些示例数据
            await self.send(text_data=json.dumps({
                'type': 'crawl_data',
                'items': [
                    {'title': '示例图片1', 'url': 'http://example.com/image1.jpg'},
                    {'title': '示例图片2', 'url': 'http://example.com/image2.jpg'},
                    {'title': '示例图片3', 'url': 'http://example.com/image3.jpg'}
                ]
            }))
            
            # 模拟下载进度
            for i in range(1, 11):
                await asyncio.sleep(1)  # 模拟下载时间
                progress = i * 10
                await self.send(text_data=json.dumps({
                    'type': 'download_progress',
                    'progress': progress,
                    'message': f'正在下载... {progress}%'
                }))
            
            # 下载完成
            await self.send(text_data=json.dumps({
                'type': 'download_complete',
                'message': '下载完成'
            }))
            
        except Exception as e:
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