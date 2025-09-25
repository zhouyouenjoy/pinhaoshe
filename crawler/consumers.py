import json
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import importlib
from django.utils import timezone
from django.core.files.base import ContentFile
import requests
from io import BytesIO
from PIL import Image
import os
# 添加Selenium相关导入
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
                spider = spiders_module.DouyinSpider(headless=False, username=username)
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
        # 获取当前的crawl_avatar状态，默认为False
        crawl_avatar = data.get('crawl_avatar', False)
        
        if not session_id or session_id not in self.active_sessions:
            await self.send_error('无效的会话ID')
            return
        
        session_data = self.active_sessions[session_id]
        spider = session_data['spider']
        # 使用传入的crawl_avatar状态而不是会话中保存的状态
        download_media = session_data.get('download_media', False)  # 获取媒体下载选项
        
        try:
            # 直接使用最新窗口
            try:
                window_handles = await sync_to_async(lambda: spider.driver.window_handles)()
                print(f"所有窗口句柄: {window_handles}")
                
                if not window_handles:
                    await self.send_error('没有可用的浏览器窗口')
                    return
                
                # 直接切换到最新窗口
                latest_window = window_handles[-1]
                await sync_to_async(lambda h=latest_window: spider.driver.switch_to.window(h))()
                
                current_url = await sync_to_async(lambda: spider.driver.current_url)()
                print(f"当前窗口URL: {current_url}")
            except Exception as e:
                print(f"获取当前窗口信息时出错: {str(e)}")
                await self.send_error(f'获取当前窗口信息失败: {str(e)}')
                return
                
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
                    # 如果#之前没有内容，则使用#号后的第一个标签作为标题
                    if not album_title and "#" in parts[1]:
                        tags = parts[1].split("#")
                        # 过滤掉空标签并获取前两个标签
                        non_empty_tags = [tag.strip() for tag in tags if tag.strip()]
                        if non_empty_tags:
                            # 使用第一个标签作为标题
                            album_title = non_empty_tags[0]
                            # 如果有第二个标签，也加入标题
                            if len(non_empty_tags) > 1:
                                album_title += " " + non_empty_tags[1]
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
            
            # 如果用户选择下载媒体文件，则下载照片和头像
            if download_media:
                await self.download_media_files(image_urls, user_avatar, final_username, session_data['platform'])
            else:
                # 即使不下载媒体文件，也发送完成消息
                await self.send(text_data=json.dumps({
                    'type': 'download_complete',
                    'message': f'处理完成，共找到 {len(image_urls)} 张图片'
                }))
            
        except Exception as e:
            print(f"下载过程中发生异常: {str(e)}")  # 添加调试日志
            # 发送错误消息，确保前端可以重新启用下载按钮
            await self.send_error(f'下载失败: {str(e)}')
                
    async def download_media_files(self, image_urls, user_avatar_url, username, platform):
        """下载媒体文件（照片和头像）"""
        try:
            # 延迟导入模型，避免在Django未完全初始化时加载模型
            from crawler.models import CrawlerUser, Album, Photo
            from PIL import Image
            import io
            
            print(f"开始下载媒体文件: {len(image_urls)} 张图片, 头像: {user_avatar_url}, 用户名: {username}")  # 添加调试日志
            
            # 获取用户和相册信息
            crawler_user = None
            album = None
            if username:
                try:
                    crawler_user = await sync_to_async(CrawlerUser.objects.using('crawler').get)(username=username)
                    album = await sync_to_async(Album.objects.using('crawler').filter(uploaded_by=crawler_user).last)()
                    print(f"找到用户: {username}, 相册: {album}")  # 添加调试日志
                except CrawlerUser.DoesNotExist:
                    print(f"用户不存在: {username}")
                except Exception as e:
                    print(f"获取用户或相册时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 计算总任务数（头像+图片）
            total_tasks = (1 if user_avatar_url and crawler_user else 0) + len(image_urls)
            completed_tasks = 0
            
            # 发送初始进度
            await self.send_progress(0, total_tasks, "开始下载...")
            
            # 下载头像
            if user_avatar_url and crawler_user:
                try:
                    print(f"开始下载头像: {user_avatar_url}")  # 添加调试日志
                    response = requests.get(user_avatar_url, timeout=30)
                    if response.status_code == 200:
                        # 创建文件名
                        avatar_filename = f"{username}_avatar_{int(timezone.now().timestamp())}.webp" if username else f"avatar_{int(timezone.now().timestamp())}.webp"
                        
                        # 处理图片格式和大小
                        img_data = response.content
                        img = Image.open(io.BytesIO(img_data))
                        
                        # 转换为RGB模式（如果需要）
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # 压缩图片（如果大于1MB）
                        img_io = io.BytesIO()
                        quality = 90
                        img.save(img_io, format='WEBP', quality=quality, method=6)
                        
                        # 检查文件大小，如果大于1MB则进一步压缩
                        while img_io.tell() > 1024 * 1024 and quality > 10:
                            img_io = io.BytesIO()
                            quality -= 10
                            img.save(img_io, format='WEBP', quality=quality, method=6)
                        
                        img_io.seek(0)
                        
                        # 将图片内容转换为Django ImageField可以处理的格式
                        img_content = ContentFile(img_io.read())
                        # 使用sync_to_async包装头像保存方法
                        await sync_to_async(crawler_user.avatar.save)(avatar_filename, img_content)
                        await sync_to_async(crawler_user.save)()
                        print(f"头像已下载并保存: {avatar_filename}")
                    else:
                        print(f"下载头像失败，状态码: {response.status_code}")
                except Exception as e:
                    print(f"下载头像时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # 更新进度
                    completed_tasks += 1
                    await self.send_progress(completed_tasks, total_tasks, f"已下载头像...")
            
            # 下载照片
            print(f"开始下载 {len(image_urls)} 张照片")  # 添加调试日志
            for i, image_url in enumerate(image_urls):
                if not album:
                    print("没有找到相册，跳过照片下载")  # 添加调试日志
                    # 更新进度
                    completed_tasks += 1
                    await self.send_progress(completed_tasks, total_tasks, f"跳过照片下载...")
                    break  # 如果没有相册，不下载照片
                    
                try:
                    print(f"正在下载第 {i+1} 张照片: {image_url}")  # 添加调试日志
                    response = requests.get(image_url, timeout=30)
                    if response.status_code == 200:
                        # 创建文件名
                        photo_filename = f"{platform}_{int(timezone.now().timestamp())}_{i+1}.webp"
                        
                        # 获取对应的照片对象
                        photo = await sync_to_async(
                            Photo.objects.using('crawler').filter(
                                album=album, 
                                external_url=image_url
                            ).first)()
                        
                        if photo:
                            # 处理图片格式和大小
                            img_data = response.content
                            img = Image.open(io.BytesIO(img_data))
                            
                            # 转换为RGB模式（如果需要）
                            if img.mode in ('RGBA', 'LA', 'P'):
                                img = img.convert('RGB')
                            
                            # 压缩图片（如果大于1MB）
                            img_io = io.BytesIO()
                            quality = 90
                            img.save(img_io, format='WEBP', quality=quality, method=6)
                            
                            # 检查文件大小，如果大于1MB则进一步压缩
                            while img_io.tell() > 1024 * 1024 and quality > 10:
                                img_io = io.BytesIO()
                                quality -= 10
                                img.save(img_io, format='WEBP', quality=quality, method=6)
                            
                            img_io.seek(0)
                            
                            # 将图片内容转换为Django ImageField可以处理的格式
                            img_content = ContentFile(img_io.read())
                            # 使用sync_to_async包装photo.image.save和photo.save调用
                            await sync_to_async(photo.image.save)(photo_filename, img_content)
                            await sync_to_async(photo.save)()
                            print(f"照片已下载并保存: {photo_filename}")
                        else:
                            print(f"未找到对应的照片对象: {image_url}")
                    else:
                        print(f"下载照片失败，状态码: {response.status_code}, URL: {image_url}")
                except Exception as e:
                    print(f"下载照片时出错 (第{i+1}张): {str(e)}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # 更新进度
                    completed_tasks += 1
                    await self.send_progress(completed_tasks, total_tasks, f"已下载 {i+1}/{len(image_urls)} 张照片")
                    
            print("媒体文件下载完成")  # 添加调试日志
            await self.send_progress(total_tasks, total_tasks, "下载完成")
            # 发送下载完成消息
            await self.send(text_data=json.dumps({
                'type': 'download_complete',
                'message': '下载完成'
            }))
        except Exception as e:
            print(f"下载媒体文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 即使出错也要发送错误消息，确保前端可以重新启用下载按钮
            await self.send_error(f'下载失败: {str(e)}')
            
    async def send_progress(self, completed, total, message=""):
        """发送进度更新消息"""
        if total > 0:
            progress = int((completed / total) * 100)
            await self.send(text_data=json.dumps({
                'type': 'download_progress',
                'progress': progress,
                'message': message or f'正在下载... {progress}%'
            }))

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
            
            # 只有在有图片时才创建相册
            if not image_urls or len(image_urls) == 0:
                print("没有图片，跳过相册创建")
                return
            
            # 创建相册（使用处理后的标题，以当前时间命名作为后备）
            album_title_final = album_title if album_title else f"{session_data['platform']} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            try:
                album = await sync_to_async(Album.objects.using('crawler').create)(
                    title=album_title_final,
                    description=album_description,
                    uploaded_by=crawler_user,
                    approved=True,  # 强制设置为True，确保所有爬虫创建的相册都默认展示
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
                        approved=True,  # 强制设置为True，确保所有爬虫创建的照片都默认展示
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

    async def download_images(self, data):
        """下载图片"""
        session_id = data.get('session_id')
        if not session_id or session_id not in self.active_sessions:
            await self.send_error('无效的会话ID')
            return

        session_data = self.active_sessions[session_id]
        driver = session_data.get('driver')
        if not driver:
            await self.send_error('未找到浏览器实例')
            return

        try:
            # 确保使用最新的窗口
            try:
                # 尝试切换到最新的窗口
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[-1])
                else:
                    await self.send_error('没有可用的浏览器窗口')
                    return
            except Exception as e:
                print(f"切换窗口时出错: {str(e)}")
                await self.send_error(f'切换窗口时出错: {str(e)}')
                return

            # 获取当前页面的所有图片元素
            images = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img"))
            )
            
            image_urls = []
            for img in images:
                # 获取图片的src属性
                src = img.get_attribute('src')
                if src and src.startswith('http'):
                    image_urls.append(src)
                # 也尝试获取data-src属性（某些网站使用懒加载）
                data_src = img.get_attribute('data-src')
                if data_src and data_src.startswith('http'):
                    image_urls.append(data_src)
            
            # 去重
            image_urls = list(dict.fromkeys(image_urls))
            
            # 发送找到的图片数量
            await self.send(text_data=json.dumps({
                'type': 'image_count',
                'count': len(image_urls)
            }))
            
            total_images = len(image_urls)
            downloaded_images = 0
            
            # 下载每张图片
            for i, url in enumerate(image_urls):
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        downloaded_images += 1
                        # 发送下载进度
                        await self.send(text_data=json.dumps({
                            'type': 'download_progress',
                            'current': downloaded_images,
                            'total': total_images,
                            'url': url
                        }))
                    else:
                        print(f"下载图片失败: {url}, 状态码: {response.status_code}")
                except Exception as e:
                    print(f"下载图片时出错: {url}, 错误: {str(e)}")
            
            # 下载完成
            await self.send(text_data=json.dumps({
                'type': 'download_complete',
                'message': f'下载完成，共下载 {total_images} 张图片'
            }))
            
        except Exception as e:
            print(f"下载过程中发生异常: {str(e)}")  # 添加调试日志
            # 发送错误消息，确保前端可以重新启用下载按钮
            await self.send_error(f'下载失败: {str(e)}')
