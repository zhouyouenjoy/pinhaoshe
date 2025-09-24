from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .models import CrawlerUser, Album, Photo
from photos.models import User, Album as PhotoAlbum, Photo as PhotoPhoto, UserProfile

# 配置日志
logger = logging.getLogger(__name__)

@login_required
def crawl_page(request):
    return render(request, 'crawler/crawl_page.html')

@login_required
def user_list(request):
    users = CrawlerUser.objects.using('crawler').all().order_by('-date_joined')
    return render(request, 'crawler/user_list.html', {'users': users})

@login_required
def user_detail(request, user_id):
    user = get_object_or_404(CrawlerUser.objects.using('crawler'), id=user_id)
    albums = Album.objects.using('crawler').filter(uploaded_by=user).order_by('-uploaded_at')
    return render(request, 'crawler/user_detail.html', {
        'crawler_user': user,
        'albums': albums
    })

@login_required
def album_detail(request, album_id):
    album = get_object_or_404(Album.objects.using('crawler'), id=album_id)
    photos = Photo.objects.using('crawler').filter(album=album).order_by('-uploaded_at')
    return render(request, 'crawler/album_detail.html', {
        'album': album,
        'photos': photos
    })

@login_required
@transaction.atomic
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(CrawlerUser.objects.using('crawler'), id=user_id)
        username = user.username
        user.delete()
        messages.success(request, f'用户 "{username}" 及其所有相关数据已成功删除。')
        return redirect('crawler:user_list')
    return redirect('crawler:user_detail', user_id=user_id)

@login_required
@transaction.atomic
def delete_album(request, album_id):
    if request.method == 'POST':
        album = get_object_or_404(Album.objects.using('crawler'), id=album_id)
        album_title = album.title
        album.delete()
        messages.success(request, f'相册 "{album_title}" 及其所有照片已成功删除。')
        return redirect('crawler:user_list')
    return redirect('crawler:user_detail', user_id=album.uploaded_by.id)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def sync_users(request):
    """
    将选中的爬虫用户及其相册、照片同步到主数据库
    """
    logger.info("sync_users函数被调用")
    try:
        data = json.loads(request.body)
        logger.info(f"收到的数据: {data}")
        user_ids = data.get('user_ids', [])
        sync_avatar = data.get('sync_avatar', True)  # 默认同步头像
        
        if not user_ids:
            logger.warning("未提供用户ID")
            return JsonResponse({'success': False, 'error': '未提供用户ID'})
        
        synced_count = 0
        
        # 遍历每个选中的用户
        for user_id in user_ids:
            logger.info(f"正在处理用户ID: {user_id}")
            # 获取爬虫数据库中的用户
            crawler_user = get_object_or_404(CrawlerUser.objects.using('crawler'), id=user_id)
            logger.info(f"找到爬虫用户: {crawler_user.username}")
            
            # 在主数据库中查找或创建用户
            try:
                main_user = User.objects.get(username=crawler_user.username)
                # 更新用户信息（如果需要）
                main_user.first_name = crawler_user.first_name
                main_user.last_name = crawler_user.last_name
                main_user.email = crawler_user.email
                main_user.is_staff = crawler_user.is_staff
                main_user.is_active = crawler_user.is_active
                main_user.is_superuser = crawler_user.is_superuser
                main_user.save()
                logger.info(f"更新现有用户: {main_user.username}")
            except User.DoesNotExist:
                # 创建新用户
                main_user = User.objects.create_user(
                    username=crawler_user.username,
                    first_name=crawler_user.first_name,
                    last_name=crawler_user.last_name,
                    email=crawler_user.email,
                    is_staff=crawler_user.is_staff,
                    is_active=crawler_user.is_active,
                    is_superuser=crawler_user.is_superuser,
                    password=crawler_user.password  # 使用相同的密码
                )
                logger.info(f"创建新用户: {main_user.username}")
            
            # 获取或创建UserProfile对象
            user_profile, created = UserProfile.objects.get_or_create(user=main_user)
            
            # 如果爬虫用户有头像URL，且用户选择同步头像，则同步到UserProfile的avatar_external_url字段
            if sync_avatar and crawler_user.avatar_url:
                user_profile.avatar_external_url = crawler_user.avatar_url
                user_profile.save()
                logger.info(f"同步用户头像: {crawler_user.avatar_url}")
            
            # 获取该用户的所有相册
            crawler_albums = Album.objects.using('crawler').filter(uploaded_by=crawler_user)
            logger.info(f"用户 {crawler_user.username} 有 {crawler_albums.count()} 个相册")
            
            # 遍历每个相册
            for crawler_album in crawler_albums:
                # 检查主数据库中是否已存在同名相册
                if PhotoAlbum.objects.filter(title=crawler_album.title, uploaded_by=main_user).exists():
                    logger.info(f"跳过已存在的相册: {crawler_album.title}")
                    continue  # 如果已存在同名相册，则跳过
                
                # 在主数据库中创建相册
                main_album = PhotoAlbum.objects.create(
                    title=crawler_album.title,
                    description=crawler_album.description,
                    uploaded_by=main_user,
                    uploaded_at=crawler_album.uploaded_at,
                    approved=crawler_album.approved,
                )
                logger.info(f"创建相册: {main_album.title}")
                
                # 获取该相册的所有照片
                crawler_photos = Photo.objects.using('crawler').filter(album=crawler_album)
                logger.info(f"相册 {crawler_album.title} 有 {crawler_photos.count()} 张照片")
                
                # 遍历每张照片
                for crawler_photo in crawler_photos:
                    # 准备照片数据，处理image字段,不要发送title字段
                    photo_data = {
                        'external_url': crawler_photo.external_url,
                        'uploaded_by': main_user,
                        'uploaded_at': crawler_photo.uploaded_at,
                        'approved': crawler_photo.approved,
                        'album': main_album,
                    }
                    
                    # 只有当image字段有关联文件时才传递该字段
                    if crawler_photo.image:
                        photo_data['image'] = crawler_photo.image
                    
                    # 在主数据库中创建照片
                    photo_obj = PhotoPhoto.objects.create(**photo_data)
                    logger.info(f"创建照片: {photo_obj.external_url}")
            
            synced_count += 1
        
        logger.info(f"成功同步 {synced_count} 个用户")
        return JsonResponse({
            'success': True, 
            'synced_count': synced_count,
            'message': f'成功同步 {synced_count} 个用户及其数据'
        })
        
    except Exception as e:
        logger.error(f"同步用户时发生错误: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def check_user_status(request):
    """
    检查用户是否存在以及是否有头像
    """
    if request.method == 'GET' and 'username' in request.GET:
        username = request.GET['username']
        try:
            # 检查用户是否存在
            user = CrawlerUser.objects.using('crawler').get(username=username)
            # 检查用户是否有头像
            has_avatar = bool(user.avatar_url)
            return JsonResponse({
                'exists': True,
                'has_avatar': has_avatar,
                'avatar_url': user.avatar_url if has_avatar else None
            })
        except CrawlerUser.DoesNotExist:
            return JsonResponse({
                'exists': False,
                'has_avatar': False,
                'avatar_url': None
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

