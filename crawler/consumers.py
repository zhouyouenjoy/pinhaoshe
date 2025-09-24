import json
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import importlib
from django.utils import timezone


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
        crawl_avatar = data.get('crawl_avatar', True)  # 默认为True，即爬取头像
        
        if not platform:
            await self.send_error('平台是必需的')
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
                'download_media': download_media,
                'crawl_avatar': crawl_avatar  # 添加头像爬取选项
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
        user_provided_username = data.get('user_provided_username')
        
        if not session_id or session_id not in self.active_sessions:
            await self.send_error('无效的会话ID')
            return
        
        session_data = self.active_sessions[session_id]
        spider = session_data['spider']
        crawl_avatar = session_data.get('crawl_avatar', True)  # 获取头像爬取选项
        
        try:
            # 让spider获取当前视窗
            current_url = await sync_to_async(lambda: spider.driver.current_url)()
            print(f"当前视窗URL: {current_url}")
            # 查找具有指定class的元素并获取图片URL
            # 使用CSS选择器查找class='wCekfc8o qxTcdFT5'的元素
            if session_data['platform'] == 'douyin':
                container_css_selector = "nM3w4mVK cmI2tyuz focusPanel"
                caption_css_selector = "arnSiSbK hT34TYMB ONzzdL2F"
                avatar_css_selector = "B0JKdzQ8 KsoclCZj sVGJfEdt"
                username_css_selector = "account-name userAccountTextHover"
                
                # 使用新方法从容器中获取图片
                image_urls = await sync_to_async(spider.get_images_from_container)(container_css_selector)
                captions = await sync_to_async(spider.get_captions_by_class)(caption_css_selector)
                
                # 根据选项决定是否获取用户头像
                user_avatar = None
                crawled_username = None
                if crawl_avatar:
                    user_avatar = await sync_to_async(spider.get_user_avatar_by_class)(avatar_css_selector)
                    crawled_username = await sync_to_async(spider.get_username_by_class)(username_css_selector)
            elif session_data['platform'] == 'xiaohongshu':
                css_selector = "div.tiktok-1yjxlq-DivItemContainer"
                # 对于其他平台，暂时保持原有逻辑
                image_urls = await sync_to_async(spider.get_images_by_class)(css_selector)
                captions = []
                user_avatar = None
                crawled_username = None
            elif session_data['platform'] == 'bilibili':
                css_selector = "div.tiktok-1yjxlq-DivItemContainer"
                # 对于其他平台，暂时保持原有逻辑
                image_urls = await sync_to_async(spider.get_images_by_class)(css_selector)
                captions = []
                user_avatar = None
                crawled_username = None
    
            # 确定使用的用户名：优先使用用户输入的用户名，否则使用爬取到的用户名
            final_username = user_provided_username if user_provided_username else crawled_username
            
            # 处理相册标题和描述
            album_title = ""
            album_description = ""
            if captions:
                # 取第一条文案进行处理
                first_caption = captions[0]
                # 按照"#"分割，第一个"#"之前的内容作为标题，之后的作为描述
                if "#" in first_caption:
                    parts = first_caption.split("#", 1)  # 只分割一次
                    album_title = parts[0].strip()
                    album_description = "#" + parts[1]  # 保留后面的#符号
                else:
                    # 如果没有#符号，则整个内容作为标题
                    album_title = first_caption.strip()
            
            # 构造返回数据
            items = []
            for i, url in enumerate(image_urls):
                items.append({
                    'title': f'图片 {i+1}',
                    'url': url,
                })
            
            # 发送找到的图片数据和相册信息
            await self.send(text_data=json.dumps({
                'type': 'crawl_data',
                'items': items,
                'album_title': album_title,
                'album_description': album_description,
                'user_avatar': user_avatar,
                'username': final_username
            }))
            
            # 保存数据到数据库
            await self.save_crawled_data(session_data, image_urls, album_title, album_description, user_avatar, final_username)
            
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
            
    async def save_crawled_data(self, session_data, image_urls, album_title, album_description, user_avatar, username):
        """将爬取的数据保存到数据库"""
        try:
            # 延迟导入模型，避免在Django未完全初始化时加载模型
            from crawler.models import CrawlerUser, Album, Photo
            
            # 获取或创建用户
            crawler_user = None
            if username:
                try:
                    crawler_user, created = await sync_to_async(CrawlerUser.objects.using('crawler').get_or_create)(
                        username=username,
                        defaults={
                            'avatar_url': user_avatar,
                            'email': '',  # 暂时为空，可以根据需要添加
                            'is_staff': False,
                            'is_active': True,
                            'is_superuser': False,
                            'password': 'pbkdf2_sha256$260000$AIgaFC17pg0j3dM65xrI0w$gcbS6m0S0I2F8wQ8S14GFgEz2nIQTM0gD5nVjE5V9uM=',  # 123456@
                        }
                    )
                    if not created and user_avatar:
                        # 如果用户已存在且有新的头像URL，则更新头像
                        crawler_user.avatar_url = user_avatar
                        await sync_to_async(crawler_user.save)()
                    print(f"用户已保存/创建: {username}, 是否新创建: {created}")
                except Exception as e:
                    print(f"保存用户时出错: {str(e)}")
                    crawler_user = None
            else:
                print("用户名为空，跳过用户创建")
            
            # 创建相册（使用处理后的标题，以当前时间命名作为后备）
            album_title_final = album_title if album_title else f"{session_data['platform']} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            try:
                album = await sync_to_async(Album.objects.using('crawler').create)(
                    title=album_title_final,
                    description=album_description,
                    uploaded_by=crawler_user,
                )
                print(f"相册已创建: {album_title_final}")
            except Exception as e:
                print(f"创建相册时出错: {str(e)}")
                return
            
            # 为每张图片创建Photo记录
            photo_count = 0
            for i, image_url in enumerate(image_urls):
                try:
                    photo_title = f"图片 {i+1}"
                    photo = await sync_to_async(Photo.objects.using('crawler').create)(
                        title=photo_title,
                        external_url=image_url,
                        uploaded_by=crawler_user,
                        album=album,
                    )
                    photo_count += 1
                    print(f"照片已创建: {photo_title}, URL: {image_url}")
                except Exception as e:
                    print(f"创建照片时出错 (第{i+1}张): {str(e)}")
            
            print(f"数据已保存到数据库: 用户={username}, 相册={album_title_final}, 照片数量={photo_count}")
            
        except Exception as e:
            print(f"保存数据到数据库时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
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