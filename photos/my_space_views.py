from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.db.models import Q
import json
from .forms import UserSpaceForm
# 从当前应用的models模块导入模型
from .models import Photo, Album, UserProfile, Comment, Like, Favorite, ViewHistory, Follow, CommentLike, PrivateMessage, Notification


@login_required
def my_info(request, user_id=None):
    """我的信息视图"""
    # 如果没有指定用户ID，则显示当前用户的信息
    if user_id is None:
        target_user = request.user
    else:
        # 否则显示指定用户的信息
        target_user = get_object_or_404(User, id=user_id)
    
    # 获取用户个人资料
    try:
        user_profile = target_user.userprofile
    except UserProfile.DoesNotExist:
        # 如果个人资料不存在，创建一个
        user_profile = UserProfile.objects.create(user=target_user)
    
    # 获取用户上传的相册
    user_albums_list = Album.objects.filter(uploaded_by=target_user).order_by('-uploaded_at')
    
    # 获取用户点赞的照片
    likes_list = Like.objects.filter(user=target_user).select_related('photo__album').order_by('-created_at')
    
    # 获取用户收藏的照片
    favorites_list = Favorite.objects.filter(user=target_user).select_related('photo__album').order_by('-created_at')
    
    # 获取用户浏览历史
    view_history_list = ViewHistory.objects.filter(user=target_user).select_related('photo__album').order_by('-viewed_at')
    
    # 检查当前用户是否已关注目标用户
    is_following = False
    if request.user != target_user:
        is_following = Follow.objects.filter(follower=request.user, followed=target_user).exists()
    
    # 获取关注数和粉丝数
    following_count = target_user.following.count()
    followers_count = target_user.followers.count()
    
    # 分页显示相册
    user_albums_paginator = Paginator(user_albums_list, 4)  # 每页4个相册
    user_albums = user_albums_paginator.get_page(1)
    
    # 分页显示点赞的照片
    likes_paginator = Paginator(likes_list, 4)  # 每页4个点赞
    likes = likes_paginator.get_page(1)
    
    # 分页显示收藏的照片
    favorites_paginator = Paginator(favorites_list, 4)  # 每页4个收藏
    favorites = favorites_paginator.get_page(1)
    
    # 分页显示浏览历史
    view_history_paginator = Paginator(view_history_list, 4)  # 每页个浏览历史
    view_history = view_history_paginator.get_page(1)
    
    # 初始化表单
    # 注意：UserSpaceForm需要从原views.py文件中导入，此处暂不实现
    
    # 渲染我的空间页面模板，并传递相关变量
    return render(request, 'photos/my_space.html', {
        'target_user': target_user,
        'user_albums': user_albums,
        'likes': likes,
        'favorites': favorites,
        'view_history': view_history,
        'is_following': is_following,
        'following_count': following_count,
        'followers_count': followers_count,
        'form': None,  # 表单部分需要额外处理
    })


@login_required
def user_albums(request, user_id):
    """显示指定用户的所有相册"""
    # 获取目标用户对象
    target_user = get_object_or_404(User, pk=user_id)
    
    # 如果是查看自己的相册，显示所有相册（包括未审核的）
    # 如果是查看他人的相册，只显示已审核的相册
    if request.user.id == user_id:
        albums_list = Album.objects.filter(uploaded_by=target_user).order_by('-uploaded_at')
    else:
        albums_list = Album.objects.filter(uploaded_by=target_user, approved=True).order_by('-uploaded_at')
    
    # 检查是否是 AJAX 请求（用于懒加载）
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = request.GET.get('page', 1)
        paginator = Paginator(albums_list, 6)  # 每页6个相册
        
        try:
            albums = paginator.page(page)
        except PageNotAnInteger:
            albums = paginator.page(1)
        except EmptyPage:
            albums = paginator.page(paginator.num_pages)
        
        # 渲染相册项目模板（用于 AJAX 加载）
        html = render_to_string('photos/user_albums_content.html', {'albums': albums, 'request': request})
        return JsonResponse({
            'html': html,
            'has_next': albums.has_next(),
            'next_page': albums.next_page_number() if albums.has_next() else None
        })
    
    # 分页显示相册
    paginator = Paginator(albums_list, 6)  # 每页6个相册
    page = request.GET.get('page', 1)
    
    try:
        albums = paginator.page(page)
    except PageNotAnInteger:
        albums = paginator.page(1)
    except EmptyPage:
        albums = paginator.page(paginator.num_pages)
    
    # 渲染模板并传递变量
    return render(request, 'photos/user_albums.html', {
        'target_user': target_user,
        'albums': albums
    })


@login_required
def user_liked_photos(request, user_id):
    """其他用户点赞的照片视图"""
    # 获取目标用户
    target_user = get_object_or_404(User, id=user_id)
    # 获取目标用户点赞的所有照片
    liked_photos_list = Photo.objects.filter(likes__user=target_user).order_by('-likes__created_at')
    
    # 检查是否是 AJAX 请求（用于懒加载）
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = request.GET.get('page', 1)
        paginator = Paginator(liked_photos_list, 6)  # 每页6个照片
        
        try:
            liked_photos = paginator.page(page)
        except PageNotAnInteger:
            liked_photos = paginator.page(1)
        except EmptyPage:
            liked_photos = paginator.page(paginator.num_pages)
        
        # 渲染照片项目模板（用于 AJAX 加载）
        html = render_to_string('photos/liked_photos_content.html', {'liked_photos': liked_photos, 'request': request})
        return JsonResponse({
            'html': html,
            'has_next': liked_photos.has_next(),
            'next_page': liked_photos.next_page_number() if liked_photos.has_next() else None
        })
    
    # 分页显示照片
    paginator = Paginator(liked_photos_list, 6)  # 每页6个照片
    page = request.GET.get('page', 1)
    
    try:
        liked_photos = paginator.page(page)
    except PageNotAnInteger:
        liked_photos = paginator.page(1)
    except EmptyPage:
        liked_photos = paginator.page(paginator.num_pages)
        
    return render(request, 'photos/liked_photos.html', {
        'liked_photos': liked_photos,
        'target_user': target_user
    })


@login_required
def user_favorited_photos(request, user_id):
    """其他用户收藏的照片视图"""
    # 获取目标用户
    target_user = get_object_or_404(User, id=user_id)
    # 获取目标用户收藏的所有照片
    favorited_photos_list = Photo.objects.filter(favorites__user=target_user).order_by('-favorites__created_at')
    
    # 检查是否是 AJAX 请求（用于懒加载）
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = request.GET.get('page', 1)
        paginator = Paginator(favorited_photos_list, 6)  # 每页6个照片
        
        try:
            favorited_photos = paginator.page(page)
        except PageNotAnInteger:
            favorited_photos = paginator.page(1)
        except EmptyPage:
            favorited_photos = paginator.page(paginator.num_pages)
        
        # 渲染照片项目模板（用于 AJAX 加载）
        html = render_to_string('photos/favorited_photos_content.html', {'favorited_photos': favorited_photos, 'request': request})
        return JsonResponse({
            'html': html,
            'has_next': favorited_photos.has_next(),
            'next_page': favorited_photos.next_page_number() if favorited_photos.has_next() else None
        })
    
    # 分页显示照片
    paginator = Paginator(favorited_photos_list, 6)  # 每页6个照片
    page = request.GET.get('page', 1)
    
    try:
        favorited_photos = paginator.page(page)
    except PageNotAnInteger:
        favorited_photos = paginator.page(1)
    except EmptyPage:
        favorited_photos = paginator.page(paginator.num_pages)
        
    return render(request, 'photos/favorited_photos.html', {
        'favorited_photos': favorited_photos,
        'target_user': target_user
    })


@login_required
def user_viewed_photos(request, user_id):
    """其他用户浏览历史视图"""
    # 获取目标用户
    target_user = get_object_or_404(User, id=user_id)
    # 获取目标用户的浏览历史
    viewed_photos_list = Photo.objects.filter(viewhistory__user=target_user).order_by('-viewhistory__viewed_at')
    
    # 检查是否是 AJAX 请求（用于懒加载）
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = request.GET.get('page', 1)
        paginator = Paginator(viewed_photos_list, 6)  # 每页6个照片
        
        try:
            viewed_photos = paginator.page(page)
        except PageNotAnInteger:
            viewed_photos = paginator.page(1)
        except EmptyPage:
            viewed_photos = paginator.page(paginator.num_pages)
        
        # 渲染照片项目模板（用于 AJAX 加载）
        html = render_to_string('photos/viewed_photos_content.html', {'viewed_photos': viewed_photos, 'request': request})
        return JsonResponse({
            'html': html,
            'has_next': viewed_photos.has_next(),
            'next_page': viewed_photos.next_page_number() if viewed_photos.has_next() else None
        })
    
    # 分页显示照片
    paginator = Paginator(viewed_photos_list, 6)  # 每页6个照片
    page = request.GET.get('page', 1)
    
    try:
        viewed_photos = paginator.page(page)
    except PageNotAnInteger:
        viewed_photos = paginator.page(1)
    except EmptyPage:
        viewed_photos = paginator.page(paginator.num_pages)
        
    return render(request, 'photos/viewed_photos.html', {
        'viewed_photos': viewed_photos,
        'target_user': target_user
    })