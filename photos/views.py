# 从django.shortcuts导入常用函数
from django.shortcuts import render, get_object_or_404, redirect
# 从django.contrib.auth.decorators导入login_required装饰器，用于限制只有登录用户才能访问
from django.contrib.auth.decorators import login_required
# 从django.contrib导入messages模块，用于显示消息提示
from django.contrib import messages
# 从django.contrib.auth导入authenticate和login函数
from django.contrib.auth import authenticate, login
# 从django.contrib.auth.models导入User模型
from django.contrib.auth.models import User
# 从django.http导入HttpResponse
from django.http import HttpResponse, JsonResponse
# 从django导入forms模块
from django import forms
# 从django.conf导入settings
from django.conf import settings
# 从django.urls导入reverse
from django.urls import reverse
# 从django.db.models导入Q用于复杂查询
from django.db.models import Q
# 从django.core.paginator导入Paginator用于分页
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
# 从当前应用的models模块导入模型
from .models import Photo, Album, UserProfile, Comment, Like, Favorite, ViewHistory, Follow, CommentLike, PrivateMessage, Notification
# 导入PIL Image模块用于处理图片
from PIL import Image
# 导入BytesIO用于处理内存中的二进制数据
from io import BytesIO
# 导入json模块用于处理JSON数据
import json
import re
from django.shortcuts import render, get_object_or_404, redirect

# 导入表单
from .forms import PhotoForm, UserRegisterForm, UserSpaceForm

# 导入get_current_site用于获取当前站点信息
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string

# 定义PhotoForm表单类
class PhotoForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='标题'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        label='描述'
    )
    images = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='选择图片',
        help_text='可选择多张图片'
    )


# 微信登录视图
def wechat_login(request):
    """
    微信登录视图 - 临时实现，后续可以替换为真正的微信登录逻辑
    """
    return render(request, 'photos/wechat_login.html')


def search(request):
    """搜索相册和用户功能"""
    query = request.GET.get('q', '')
    albums = []
    users = []
    
    if query:
        # 搜索相册（根据标题关键字）
        albums = Album.objects.filter(
            Q(title__icontains=query) & Q(approved=True)
        ).order_by('-uploaded_at')
        
        # 搜索用户（根据用户名）
        users = User.objects.filter(username__icontains=query).order_by('username')
    
    context = {
        'query': query,
        'albums': albums,
        'users': users,
    }
    return render(request, 'photos/search_results.html', context)


def custom_login(request):
    """自定义登录视图，提供详细的错误信息"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # 检查用户名是否存在
        if not User.objects.filter(username=username).exists():
            messages.error(request, '用户名不存在！')
            return render(request, 'registration/login.html')
        
        # 验证用户名和密码
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, '登录成功！')
            # 重定向到首页
            return redirect('/')
        else:
            messages.error(request, '密码错误！')
            return render(request, 'registration/login.html')
    else:
        # GET请求显示登录表单
        return render(request, 'registration/login.html')


def register(request):
    """用户注册视图"""
    # 判断请求方法是POST还是GET
    if request.method == 'POST':
        # 如果是POST请求，处理用户提交的注册信息
        form = UserRegisterForm(request.POST, request.FILES)
        # 验证表单数据是否有效
        if form.is_valid():
            # 从表单获取数据
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            avatar = form.cleaned_data['avatar']
            
            # 创建用户
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # 获取或创建用户个人资料
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            
            # 如果上传了头像，则更新头像
            if avatar:
                user_profile.avatar = avatar
                user_profile.save()
            
            # 添加成功消息
            messages.success(request, '注册成功！请登录。')
            # 重定向到登录页面
            return redirect('login')
    else:
        # 如果是GET请求，显示空的注册表单
        form = UserRegisterForm()
    # 渲染注册页面模板，并传递表单对象
    return render(request, 'photos/register.html', {'form': form})


@login_required
def upload_photo(request):
    """上传照片视图"""
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            # 获取表单数据
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            images = request.FILES.getlist('images')  # 获取所有上传的图片
            
            # 为本次上传创建一个相册
            album = Album(
                title=title,
                description=description,
                uploaded_by=request.user
            )
            album.save()
            
            # 遍历所有上传的图片，将它们都关联到同一个相册
            for image in images:
                # 为每张图片创建Photo对象
                photo = Photo(
                    title=title,
                    description=description,
                    image=image,
                    uploaded_by=request.user,
                    album=album  # 关联到相册
                )
                photo.save()
            
            # 添加成功消息
            messages.success(request, '照片上传成功！')
            # 重定向到首页
            return redirect('photos:gallery')
    else:
        form = PhotoForm()
    return render(request, 'photos/upload.html', {'form': form})


def photo_detail(request, pk):
    """照片详情视图"""
    # 获取指定ID的照片对象，如果不存在则返回404错误
    photo = get_object_or_404(Photo, pk=pk)
    
    # 获取该照片所属相册的所有照片
    if photo.album:
        photos = Photo.objects.filter(album=photo.album).order_by('id')
    else:
        photos = [photo]
    
    # 如果用户已登录，记录浏览历史
    if request.user.is_authenticated:
        view_history, created = ViewHistory.objects.get_or_create(
            user=request.user,
            photo=photo
        )
        if not created:
            # 如果记录已存在，更新浏览时间
            view_history.save()  # 会自动更新viewed_at字段
    
    
    # 检查用户是否已点赞、收藏该照片
    user_liked = False
    user_favorited = False
    is_following = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, photo=photo).exists()
        user_favorited = Favorite.objects.filter(user=request.user, photo=photo).exists()
        # 检查当前用户是否关注了照片上传者
        is_following = Follow.objects.filter(follower=request.user, followed=photo.uploaded_by).exists()
    
    context = {
        'photo': photo,
        'photos': photos,
        'user_liked': user_liked,
        'user_favorited': user_favorited,
        'is_following': is_following,
    }
    return render(request, 'photos/detail.html', context)


def album_detail(request, pk):
    """相册详情视图"""
    album = get_object_or_404(Album, pk=pk)
    photos = album.photo_set.all()
    return render(request, 'photos/album_detail.html', {'album': album, 'photos': photos})


@login_required
def my_photos(request):
    """我的照片视图"""
    # 获取当前用户上传的所有照片
    photos = Photo.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    # 渲染我的照片页面模板，并传递照片列表
    return render(request, 'photos/my_photos.html', {'photos': photos})


@login_required
def delete_photo(request, photo_id):
    """删除照片视图"""
    # 获取要删除的照片对象
    photo = get_object_or_404(Photo, id=photo_id)
    # 检查照片是否属于当前用户
    if photo.uploaded_by != request.user:
        # 如果不是，显示错误消息并重定向到我的照片页面
        messages.error(request, '您没有权限删除这张照片。')
        return redirect('my_photos')
    
    # 如果是POST请求，执行删除操作
    if request.method == 'POST':
        photo.delete()
        # 添加成功消息
        messages.success(request, '照片删除成功。')
        return redirect('my_photos')
    
    # 如果是GET请求，显示确认页面
    return render(request, 'photos/delete_photo.html', {'photo': photo})


@login_required
def delete_album(request, album_id):
    """删除相册视图"""
    # 获取要删除的相册对象
    album = get_object_or_404(Album, id=album_id)
    # 检查相册是否属于当前用户
    if album.uploaded_by != request.user:
        # 如果不是，显示错误消息并重定向到用户相册页面
        messages.error(request, '您没有权限删除这个相册。')
        return redirect('photos:user_albums', user_id=request.user.id)
    
    # 如果是POST请求，执行删除操作
    if request.method == 'POST':
        album.delete()
        # 添加成功消息
        messages.success(request, '相册删除成功。')
        return redirect('photos:user_albums', user_id=request.user.id)
    
    # 如果是GET请求，显示确认页面
    return render(request, 'photos/delete_album.html', {'album': album})


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
    
    # 获取用户上传的相册（最多4个）
    user_albums = Album.objects.filter(uploaded_by=target_user).order_by('-uploaded_at')[:4]
    
    # 获取用户的点赞、收藏和浏览历史
    likes = Like.objects.filter(user=target_user).select_related('photo')
    favorites = Favorite.objects.filter(user=target_user).select_related('photo')
    view_history = ViewHistory.objects.filter(user=target_user)[:8]
    
    # 检查当前用户是否关注了目标用户
    is_following = False
    if request.user.is_authenticated and request.user != target_user:
        is_following = Follow.objects.filter(follower=request.user, followed=target_user).exists()
    
    # 统计关注数和粉丝数
    following_count = target_user.following.count()
    followers_count = target_user.followers.count()
    
    # 处理表单提交
    if request.method == 'POST' and target_user == request.user:
        form = UserSpaceForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            # 同时更新用户名和邮箱
            target_user.username = form.cleaned_data['username']
            target_user.email = form.cleaned_data['email']
            target_user.save()
            messages.success(request, '信息更新成功！')
            return redirect('photos:my_info_with_id', user_id=target_user.id)
    else:
        # 初始化表单
        if target_user == request.user:
            initial_data = {
                'username': target_user.username,
                'email': target_user.email
            }
            if hasattr(target_user, 'userprofile') and target_user.userprofile.avatar:
                initial_data['avatar'] = target_user.userprofile.avatar
            form = UserSpaceForm(initial=initial_data, user=target_user)
        else:
            form = None
    
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
        'form': form,
    })


@login_required
def following_albums(request):
    """显示关注用户的最新相册"""
    # 获取当前用户关注的用户
    following_users = User.objects.filter(followers__follower=request.user)
    
    # 获取所有已批准的相册，并按上传时间倒序排列
    albums_list = Album.objects.filter(
        uploaded_by__in=following_users,
        approved=True
    ).order_by('-uploaded_at').select_related('uploaded_by')
    
    page = request.GET.get('page', 1)
    paginator = Paginator(albums_list, 6)  # 每页7个相册

    if page == 1: 
        try:
            albums = paginator.page(page)
        except PageNotAnInteger:
            albums = paginator.page(1)
        except EmptyPage:
            albums = paginator.page(paginator.num_pages)
        
        context = {
            'following_users': following_users,
            'albums': albums
        }
        return render(request, 'photos/following_albums.html', context)
    
    try:
        albums = paginator.page(page)
    except PageNotAnInteger:
        albums = paginator.page(1)
    except EmptyPage:
        albums = paginator.page(paginator.num_pages)
    
    # 渲染相册项目模板（用于 AJAX 加载）
    html = render_to_string('photos/following_albums_content.html', {'albums': albums, 'request': request})
    return JsonResponse({
        'html': html,
        'has_next': albums.has_next(),
        'next_page': albums.next_page_number() if albums.has_next() else None
    })
    
    


def gallery(request):
    """展示所有已批准的相册，每组只显示第一张照片"""
    # 获取所有已批准的相册，并按上传时间倒序排列
    albums_list = Album.objects.filter(approved=True).order_by('-uploaded_at')
    
    # 检查是否是 AJAX 请求（用于懒加载）
    
    page = request.GET.get('page', 1)
    paginator = Paginator(albums_list, 6)  # 每页6个相册
    if page == 1:
        try:
            albums = paginator.page(page)
        except PageNotAnInteger:
            albums = paginator.page(1)
        except EmptyPage:
            albums = paginator.page(paginator.num_pages)
        
        # 渲染photos/gallery.html模板，并传递albums变量
        return render(request, 'photos/gallery.html', {'albums': albums})
         
    try:
        albums = paginator.page(page)
    except PageNotAnInteger:
        albums = paginator.page(1)
    except EmptyPage:
        albums = paginator.page(paginator.num_pages)
    
    # 渲染相册项目模板（用于 AJAX 加载）
    html = render_to_string('photos/gallery_items.html', {'albums': albums, 'request': request})
    return JsonResponse({
        'html': html,
        'has_next': albums.has_next(),
        'next_page': albums.next_page_number() if albums.has_next() else None
    })

    





@login_required
def toggle_like(request, photo_id):
    """切换点赞状态视图"""
    if request.method == 'POST':
        # 获取照片对象
        photo = get_object_or_404(Photo, id=photo_id)
        # 获取或创建点赞记录
        like, created = Like.objects.get_or_create(user=request.user, photo=photo)
        
        # 如果记录已存在，则删除（取消点赞），否则保留（点赞）
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        # 获取照片的总点赞数
        like_count = photo.likes.count()
        
        # 返回JSON响应
        return JsonResponse({'liked': liked, 'like_count': like_count})
    
    # 如果不是POST请求，返回404错误
    return HttpResponse(status=404)


@login_required
def toggle_favorite(request, photo_id):
    """切换收藏状态视图"""
    if request.method == 'POST':
        # 获取照片对象
        photo = get_object_or_404(Photo, id=photo_id)
        # 获取或创建收藏记录
        favorite, created = Favorite.objects.get_or_create(user=request.user, photo=photo)
        
        # 如果记录已存在，则删除（取消收藏），否则保留（收藏）
        if not created:
            favorite.delete()
            favorited = False
        else:
            favorited = True
        
        # 获取照片的总收藏数
        favorite_count = photo.favorites.count()
        
        # 返回JSON响应
        return JsonResponse({'favorited': favorited, 'favorite_count': favorite_count})
    
    # 如果不是POST请求，返回404错误
    return HttpResponse(status=404)


@login_required
def toggle_follow(request, user_id):
    """切换关注状态视图"""
    if request.method == 'POST':
        # 获取目标用户
        target_user = get_object_or_404(User, id=user_id)
        
        # 不能关注自己
        if request.user == target_user:
            return JsonResponse({'error': '不能关注自己'}, status=400)
        
        # 获取或创建关注关系
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=target_user)
        
        # 如果记录已存在，则删除（取消关注），否则保留（关注）
        if not created:
            follow.delete()
            is_following = False
        else:
            is_following = True
        
        # 统计关注数和粉丝数
        following_count = target_user.followers.count()
        followers_count = target_user.following.count()
        
        # 返回JSON响应
        return JsonResponse({
            'is_following': is_following,
            'following_count': following_count,
            'followers_count': followers_count
        })
    
    # 如果不是POST请求，返回404错误
    return HttpResponse(status=404)


@login_required
def add_comment(request, photo_id):
    """添加评论视图"""
    if request.method == 'POST':
        # 获取照片对象
        photo = get_object_or_404(Photo, id=photo_id)
        # 获取评论内容
        content = request.POST.get('content')
        # 获取父评论ID（用于回复）
        parent_id = request.POST.get('parent_id')
        
        # 检查评论内容是否为空
        if content:
            # 准备创建评论的参数
            comment_params = {
                'photo': photo,
                'user': request.user,
                'content': content
            }
            
            # 如果有父评论ID，则添加parent参数
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment_params['parent'] = parent_comment
            
            # 创建评论
            comment = Comment.objects.create(**comment_params)
            
            # 检测评论中是否有@用户
            mentioned_users = set()
            # 使用支持中英文用户名的正则表达式
            pattern = r'@([a-zA-Z0-9_.\-\u4e00-\u9fa5]+)'
            matches = re.findall(pattern, content)
            
            for username in matches:
                try:
                    user = User.objects.get(username=username)
                    # 不通知自己
                    if user != request.user:
                        mentioned_users.add(user)
                except User.DoesNotExist:
                    pass  # 用户不存在，忽略
            
            # 为被@的用户创建通知
            for mentioned_user in mentioned_users:
                # 创建通知
                Notification.objects.create(
                    recipient=mentioned_user,
                    sender=request.user,
                    notification_type='mention',
                    content=f'{request.user.username} 在评论中提到了你: {content[:50]}{"..." if len(content) > 50 else ""}',
                    related_object_id=comment.id
                )
            
            # 检查是否是AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # 准备用户头像URL
                avatar_url = None
                if hasattr(request.user, 'userprofile') and request.user.userprofile.avatar:
                    avatar_url = request.user.userprofile.avatar.url
                
                # 返回JSON响应
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': request.user.id,
                    'username': request.user.username,
                    'avatar_url': avatar_url
                })
            
            messages.success(request, '评论添加成功！' if not parent_id else '回复添加成功！')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '评论内容不能为空！'}, status=400)
            messages.error(request, '评论内容不能为空！')
        
        # 重定向到照片详情页面
        return redirect('photo_detail', pk=photo_id)
    
    # 如果不是POST请求，返回404错误
    return HttpResponse(status=404)


@login_required
def delete_comment(request, comment_id):
    """删除评论视图"""
    # 获取要删除的评论对象
    print("kkkkkkkk")
    comment = get_object_or_404(Comment, id=comment_id)
    
    # 检查评论是否属于当前用户
    if comment.user != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': '您没有权限删除这条评论。'}, status=403)
        messages.error(request, '您没有权限删除这条评论。')
        return redirect('photo_detail', pk=comment.photo.id)
    
    # 获取照片ID用于重定向
    photo_id = comment.photo.id
    
    # 删除评论
    comment.delete()
    
    # 检查是否是AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 返回JSON响应
        return JsonResponse({
            'success': True,
            'message': '评论删除成功。'
        })
    
    messages.success(request, '评论删除成功。')
    
    # 重定向到照片详情页面
    return redirect('photo_detail', pk=photo_id)


@login_required
def reply_comment(request, comment_id):
    """回复评论视图"""
    if request.method == 'POST':
        # 获取父评论对象
        parent_comment = get_object_or_404(Comment, id=comment_id)
        # 获取回复内容
        content = None
        
        # 检查是否是JSON请求
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                content = data.get('content')
            except json.JSONDecodeError:
                content = None
        else:
            # 传统表单提交方式或统一表单方式
            content = request.POST.get('content')
        
        # 检查回复内容是否为空
        if content:
            # 创建回复评论
            comment = Comment.objects.create(
                photo=parent_comment.photo,
                user=request.user,
                content=content,
                parent=parent_comment
            )
            
            # 检测评论中是否有@用户
            mentioned_users = set()
            # 使用支持中英文用户名的正则表达式
            pattern = r'@([a-zA-Z0-9_.\-\u4e00-\u9fa5]+)'
            matches = re.findall(pattern, content)
            
            for username in matches:
                try:
                    user = User.objects.get(username=username)
                    # 不通知自己
                    if user != request.user:
                        mentioned_users.add(user)
                except User.DoesNotExist:
                    pass  # 用户不存在，忽略
            
            # 为被@的用户创建通知
            for mentioned_user in mentioned_users:
                # 创建通知
                Notification.objects.create(
                    recipient=mentioned_user,
                    sender=request.user,
                    notification_type='mention',
                    content=f'{request.user.username} 在回复中提到了你: {content[:50]}{"..." if len(content) > 50 else ""}',
                    related_object_id=comment.id
                )
            
            # 检查是否是AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # 准备用户头像URL
                avatar_url = None
                if hasattr(request.user, 'userprofile') and request.user.userprofile.avatar:
                    avatar_url = request.user.userprofile.avatar.url
                
                # 返回JSON响应
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': request.user.id,
                    'username': request.user.username,
                    'avatar_url': avatar_url
                })
            
            messages.success(request, '回复添加成功！')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '回复内容不能为空！'}, status=400)
            messages.error(request, '回复内容不能为空！')
        
        # 重定向到照片详情页面
        return redirect('photo_detail', pk=parent_comment.photo.id)
    
    # 如果不是POST请求，返回404错误
    return HttpResponse(status=404)


@login_required
def toggle_comment_like(request, comment_id):
    """切换评论点赞状态视图"""
    if request.method == 'POST':
        # 获取评论对象
        comment = get_object_or_404(Comment, id=comment_id)
        # 获取或创建评论点赞记录
        like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        
        # 如果记录已存在，则删除（取消点赞），否则保留（点赞）
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        # 获取评论的总点赞数
        like_count = comment.get_like_count()
        
        # 返回JSON响应
        return JsonResponse({'liked': liked, 'like_count': like_count})
    
    # 如果不是POST请求，返回404错误
    return HttpResponse(status=404)


#这个应该采用懒加载，是评论区的加载。
def get_comment_tree(request, photo_id):
    """获取照片评论树"""
    photo = get_object_or_404(Photo, id=photo_id)
    # 获取顶级评论（没有parent的评论），按创建时间倒序排列（最新评论在前）
    comments = Comment.objects.filter(photo=photo, parent=None).order_by('-created_at')

# 定义递归函数处理所有层级的回复
    def set_liked_status(comment, user):
        comment.is_liked = comment.comment_likes.filter(user=user).exists()
        # 获取当前评论的直接回复
        replies = comment.replies.all().order_by('-created_at')
        # 递归处理每条回复（包括回复的回复）
        for reply in replies:
            set_liked_status(reply, user)  # 这里会处理 reply 的 processed_replies
        # 赋值给当前评论
        comment.processed_replies = replies  # 包含所有处理好的子回复

    # 为每个主评论及其所有嵌套回复设置点赞状态
    for comment in comments:
        set_liked_status(comment, request.user)
    
    # 如果是AJAX请求，返回JSON格式的评论树
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        def serialize_comment(comment):
            """序列化单个评论"""
            avatar_url = None
            if hasattr(comment.user, 'userprofile') and comment.user.userprofile.avatar:
                avatar_url = comment.user.userprofile.avatar.url
                
            # 获取回复，按创建时间倒序排列（最新的回复在前）
            replies = comment.replies.all().order_by('-created_at')
            
            return {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': comment.user.id,
                'username': comment.user.username,
                'avatar_url': avatar_url,
                'like_count': comment.get_like_count(),
                'user_authenticated': request.user.is_authenticated,
                'replies': [serialize_comment(reply) for reply in replies]
            }
        
        comment_tree = [serialize_comment(comment) for comment in comments]
        return JsonResponse({'comments': comment_tree})
    
    # 否则渲染模板
    context = {
        'photo': photo,
        'comments': comments,
    }
    return render(request, 'photos/comment_list.html', context)


@login_required
def liked_photos(request):
    """用户点赞的照片视图"""
    # 获取当前用户点赞的所有照片
    liked_photos = Photo.objects.filter(likes__user=request.user).order_by('-likes__created_at')
    return render(request, 'photos/liked_photos.html', {'liked_photos': liked_photos})


@login_required
def favorited_photos(request):
    """用户收藏的照片视图"""
    # 获取当前用户收藏的所有照片
    favorited_photos = Photo.objects.filter(favorites__user=request.user).order_by('-favorites__created_at')
    return render(request, 'photos/favorited_photos.html', {'favorited_photos': favorited_photos})


@login_required
def viewed_photos(request):
    """用户浏览历史视图"""
    # 获取当前用户的浏览历史
    viewed_photos = Photo.objects.filter(viewhistory__user=request.user).order_by('-viewhistory__viewed_at')
    return render(request, 'photos/viewed_photos.html', {'viewed_photos': viewed_photos})


# 发送私信视图
@login_required
def send_message(request, recipient_id):
    """
    发送私信视图
    """
    recipient = get_object_or_404(User, id=recipient_id)
    
    # 不能给自己发私信
    if request.user == recipient:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': '不能给自己发送私信！'}, status=400)
        messages.error(request, '不能给自己发送私信！')
        return redirect('photos:my_info_with_id', user_id=recipient_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if not content:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': '私信内容不能为空！'
                }, status=400)
            messages.error(request, '私信内容不能为空！')
            return render(request, 'photos/send_message.html', {
                'recipient': recipient,
                'content': content
            })
        
        try:
            # 创建私信
            message = PrivateMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content
            )
            
            # 如果是AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sent_at': message.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'sender': message.sender.username
                    }
                })
            
            messages.success(request, '私信发送成功！')
            return redirect('photos:my_info_with_id', user_id=recipient_id)
        except Exception as e:
            # 捕获数据库错误等异常
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': '发送私信时发生错误: {}'.format(str(e))
                }, status=500)
            messages.error(request, '发送私信时发生错误: {}'.format(str(e)))
            return render(request, 'photos/send_message.html', {
                'recipient': recipient,
                'content': content
            })
    
    # GET请求：显示发送私信表单
    return render(request, 'photos/send_message.html', {
        'recipient': recipient
    })


# 私信列表视图
@login_required
def messages_list(request):
    """消息列表视图，包括私信和通知"""
    # 检查是否是AJAX请求用于下滑加载
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # 获取所有与当前用户相关的私信（作为发送者或接收者）
    all_messages = PrivateMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')
    
    # 按联系人分组，获取每个对话的最新消息
    conversations = {}
    for message in all_messages:
        # 确定对话的另一方
        other_user = message.sender if message.recipient == request.user else message.recipient
        
        # 如果该联系人还没有对话记录，或者当前消息比已记录的消息更新
        if other_user not in conversations or message.sent_at > conversations[other_user].sent_at:
            conversations[other_user] = message
    
    # 转换为按时间排序的列表
    all_conversations = sorted(conversations.values(), key=lambda x: x.sent_at, reverse=True)
    
    # 获取用户的通知
    notifications = request.user.notifications.all()
    
    # 将通知按类型分组
    like_and_favorite_notifications = notifications.filter(
        notification_type__in=['like', 'favorite']
    ).order_by('-created_at')
    
    comment_and_mention_notifications = notifications.filter(
        notification_type__in=['comment', 'reply', 'mention', 'comment_like']
    ).order_by('-created_at')
    
    follow_notifications = notifications.filter(
        notification_type='follow'
    ).order_by('-created_at')
    
    other_notifications = notifications.filter(
        notification_type__in=['message']
    ).order_by('-created_at')
    
    # 为mention类型的通知添加comment属性
    for notification in notifications:
        if notification.notification_type == 'mention' and notification.related_object_id:
            try:
                comment = Comment.objects.select_related('photo').get(id=notification.related_object_id)
                notification.comment = comment
            except Comment.DoesNotExist:
                notification.comment = None
        else:
            notification.comment = None
    
    # 也为comment, reply和comment_like类型的通知添加相关对象属性
    for notification in notifications:
        if notification.notification_type in ['comment', 'reply'] and notification.related_object_id:
            try:
                comment = Comment.objects.select_related('photo').get(id=notification.related_object_id)
                notification.comment = comment
            except Comment.DoesNotExist:
                notification.comment = None
        elif notification.notification_type == 'comment_like' and notification.related_object_id:
            try:
                comment_like = CommentLike.objects.select_related('comment__photo').get(id=notification.related_object_id)
                notification.comment_like = comment_like
            except CommentLike.DoesNotExist:
                notification.comment_like = None
        else:
            if not hasattr(notification, 'comment'):
                notification.comment = None
            if not hasattr(notification, 'comment_like'):
                notification.comment_like = None
    
    # 获取置顶对话
    pinned_conversations = request.user.userprofile.pinned_conversation_records.all()
    pinned_ids = [pc.other_user.id for pc in pinned_conversations]
    
    # 将对话分为置顶和普通两组
    pinned_messages = []
    normal_messages = []
    for msg in all_conversations:
        other_user = msg.sender if msg.recipient == request.user else msg.recipient
        if other_user.id in pinned_ids:
            pinned_messages.append(msg)
        else:
            normal_messages.append(msg)
    
    # 合并列表，置顶对话在前
    all_messages = pinned_messages + normal_messages
    
    # 计算未读私信数量
    unread_messages_count = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
    
    # 计算各类未读通知数量
    unread_like_favorite_count = like_and_favorite_notifications.filter(is_read=False).count()
    unread_comment_mention_count = comment_and_mention_notifications.filter(is_read=False).count()
    unread_follow_count = follow_notifications.filter(is_read=False).count()
    
    # 分页处理所有对话消息
    message_paginator = Paginator(all_messages, 10)  # 每页显示10条对话
    message_page = request.GET.get('message_page', 1)  # 默认显示第1页
    messages_page = message_paginator.get_page(message_page)
    #991 如果是AJAX请求且不是第一页，使用正确的offset获取下一页数据
    if is_ajax and message_page != '1':
        # 获取当前页码的整数值
        current_page = int(message_page)
        # 获取下一页数据的起始位置
        offset = (current_page - 1) * 10
        # 确保offset不超过总数据量
        if offset < len(all_messages):
            messages_page = all_messages[offset:offset+10]
        else:
            messages_page = []
    else:
        # 非AJAX请求或第一页，使用标准分页
        messages_page = message_paginator.get_page(message_page)
    
    # 分页处理各类通知
    like_favorite_paginator = Paginator(like_and_favorite_notifications, 10)
    like_favorite_page = request.GET.get('like_favorite_page', 1)  # 默认显示第1页
    like_favorite_notifications_page = like_favorite_paginator.get_page(like_favorite_page)
    
    comment_mention_paginator = Paginator(comment_and_mention_notifications, 10)
    comment_mention_page = request.GET.get('comment_mention_page', 1)  # 默认显示第1页
    comment_mention_notifications_page = comment_mention_paginator.get_page(comment_mention_page)
    
    follow_paginator = Paginator(follow_notifications, 10)
    follow_page = request.GET.get('follow_page', 1)  # 默认显示第1页
    follow_notifications_page = follow_paginator.get_page(follow_page)
    
    # 如果是AJAX请求，返回对应标签页的内容
    if is_ajax:
        # 确定请求的是哪个标签页
        partial = request.GET.get('partial', 'private-messages')
        from django.template.loader import render_to_string
        
        # 根据请求的标签页返回对应的内容
        if partial == 'private-messages':
            context = {'all_messages': messages_page}
            html_content = render_to_string('photos/messages_list.html', context, request=request)
            return HttpResponse(html_content)
        elif partial == 'like-favorite':
            context = {'like_favorite_notifications': like_favorite_notifications_page}
            html_content = render_to_string('photos/messages_list.html', context, request=request)
            return HttpResponse(html_content)
        elif partial == 'comment-mention':
            context = {'comment_mention_notifications': comment_mention_notifications_page}
            html_content = render_to_string('photos/messages_list.html', context, request=request)
            return HttpResponse(html_content)
        elif partial == 'follow-notifications':
            context = {'follow_notifications': follow_notifications_page}
            html_content = render_to_string('photos/messages_list.html', context, request=request)
            return HttpResponse(html_content)
        elif partial == 'messages':
            # 创建只包含当前页数据的上下文字典
            context = {
                'all_messages': messages_page,
                'unread_messages_count': unread_messages_count,
            }
            html_content = render_to_string('photos/messages_list.html', context, request=request)
            return HttpResponse(html_content)
        #如果是AJAX请求且不是第一页，并且没有数据了，返回空内容
        if is_ajax and message_page != '1' and not messages_page:
                return HttpResponse('')
    
    return render(request, 'photos/messages_list.html', {
        'all_messages': messages_page,
        'like_favorite_notifications': like_favorite_notifications_page,
        'comment_mention_notifications': comment_mention_notifications_page,
        'follow_notifications': follow_notifications_page,
        'other_notifications': other_notifications,
        'unread_messages_count': unread_messages_count,
        'unread_like_favorite_count': unread_like_favorite_count,
        'unread_comment_mention_count': unread_comment_mention_count,
        'unread_follow_count': unread_follow_count
    })


def chat_view(request, recipient_id):
    """
    直接进入聊天视图
    """
    recipient = get_object_or_404(User, id=recipient_id)
    
    # 不能给自己发私信
    if request.user == recipient:
        messages.error(request, '不能给自己发送私信！')
        return redirect('my_info_with_id', user_id=recipient_id)
    
    # 查找或创建一个初始消息
    # 先尝试查找已有的对话
    existing_message = PrivateMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=recipient)) |
        (Q(sender=recipient) & Q(recipient=request.user))
    ).order_by('-sent_at').first()
    
    # 如果没有现有对话，则创建一个初始消息
    if not existing_message:
        # 创建一个空的初始消息
        initial_message = PrivateMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            content=f"与 {recipient.username} 的对话已建立"
        )
        message_id = initial_message.id
    else:
        message_id = existing_message.id
    
    # 重定向到消息详情页面
    return redirect('photos:message_detail', message_id=message_id)


def message_detail(request, message_id):
    """
    显示私信详情，包括双方的历史交流记录
    """
    current_message = get_object_or_404(PrivateMessage, id=message_id)
    
    # 只有发送者或接收者可以查看私信
    if request.user != current_message.sender and request.user != current_message.recipient:
        messages.error(request, '您没有权限查看此私信！')
        return redirect('messages_list')
    
    # 标记为已读
    if request.user == current_message.recipient and not current_message.is_read:
        current_message.is_read = True
        current_message.save()
    
    # 获取双方的交流历史，按时间倒序排列（最新的在最上面）
    other_user = current_message.sender if request.user == current_message.recipient else current_message.recipient
    conversation = PrivateMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('-sent_at')
    
    return render(request, 'photos/message_detail.html', {
        'message': current_message,
        'conversation': conversation
    })


@login_required
def load_more_messages(request):
    """
    加载更多私信消息（用于懒加载）
    """
    if request.method != 'GET':
        return JsonResponse({'error': '无效请求方法'}, status=400)
    
    try:
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 10))
        recipient_id = int(request.GET.get('recipient_id'))
    except (ValueError, TypeError):
        return JsonResponse({'error': '参数错误'}, status=400)
    
    # 获取对方用户
    other_user = get_object_or_404(User, id=recipient_id)
    
    # 获取双方的交流历史，按时间倒序排列
    conversation = PrivateMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('-sent_at')[offset:offset+limit]
    
    # 构造返回数据
    messages_data = []
    for msg in conversation:
        # 获取发送者头像URL
        sender_avatar_url = None
        if hasattr(msg.sender, 'userprofile') and msg.sender.userprofile.avatar:
            sender_avatar_url = msg.sender.userprofile.avatar.url
        
        messages_data.append({
            'id': msg.id,
            'content': msg.content.replace('\n', '<br>'),
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'sender_avatar': sender_avatar_url,
            'is_own': msg.sender == request.user,
            'is_read': msg.is_read
        })
    
    return JsonResponse({
        'messages': messages_data
    })


@login_required
def check_new_messages(request):
    """
    检查是否有新消息（用于短轮询）
    """
    if request.method != 'GET':
        return JsonResponse({'error': '无效请求方法'}, status=400)
    
    try:
        last_message_id = int(request.GET.get('last_message_id', 0))
        recipient_id = int(request.GET.get('recipient_id'))
    except (ValueError, TypeError):
        return JsonResponse({'error': '参数错误'}, status=400)
    
    # 获取对方用户
    other_user = get_object_or_404(User, id=recipient_id)
    
    # 获取对方发送的新消息（ID大于last_message_id的消息）
    new_messages = PrivateMessage.objects.filter(
        sender=other_user,
        recipient=request.user,
        id__gt=last_message_id
    ).order_by('sent_at')
    
    # 标记新消息为已读
    for message in new_messages:
        if not message.is_read:
            message.is_read = True
            message.save()
    
    # 构造返回数据
    messages_data = []
    for msg in new_messages:
        # 获取发送者头像URL
        sender_avatar_url = None
        if hasattr(msg.sender, 'userprofile') and msg.sender.userprofile.avatar:
            sender_avatar_url = msg.sender.userprofile.avatar.url
        
        messages_data.append({
            'id': msg.id,
            'content': msg.content.replace('\n', '<br>'),
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'sender_avatar': sender_avatar_url,
            'is_own': False,  # 对方发送的消息
            'is_read': msg.is_read
        })
    
    return JsonResponse({
        'messages': messages_data
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


@login_required
def mark_messages_as_read(request):
    """批量标记私信为已读"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            
            # 批量更新符合条件的消息
            updated = PrivateMessage.objects.filter(
                id__in=message_ids,
                recipient=request.user,
                is_read=False
            ).update(is_read=True)
            
            # 更新未读私信计数
            unread_count = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
            
            return JsonResponse({
                'success': True,
                'updated_count': updated,
                'unread_count': unread_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': '只支持POST请求'
    }, status=400)

@login_required
def mark_message_as_read(request, message_id):
    """标记单条私信为已读"""
    if request.method == 'POST':
        try:
            message = get_object_or_404(PrivateMessage, id=message_id, recipient=request.user)
            message.is_read = True
            message.save(update_fields=['is_read'])
            
            # 更新未读私信计数
            unread_count = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
            
            return JsonResponse({
                'success': True,
                'unread_count': unread_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': '只支持POST请求'
    }, status=400)

@login_required
def mark_notification_as_read(request, notification_id):
    """标记通知为已读"""
    print(f"\n=== 标记通知请求开始 ===")
    print(f"方法: {request.method}")
    print(f"用户: {request.user.username if request.user.is_authenticated else '未认证'}")
    print(f"请求头: {dict(request.headers)}")
    print(f"请求体: {request.body}")
    
    if request.method == 'POST':
        print(f"\n处理通知ID: {notification_id}")
        try:
            # 先检查通知是否存在
            notification = get_object_or_404(Notification, id=notification_id)
            print(f"找到通知 - 接收者: {notification.recipient.username}")
            
            # 检查当前用户是否是通知接收者
            if notification.recipient != request.user:
                print(f"警告: 用户{request.user.username}尝试标记不属于自己的通知为已读")
                return JsonResponse({
                    'success': False, 
                    'error': '无权操作此通知'
                }, status=403)
            
            print(f"原始状态 - is_read: {notification.is_read}")
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            
            # 验证是否保存成功
            updated_notification = Notification.objects.get(id=notification_id)
            print(f"更新后状态 - is_read: {updated_notification.is_read}")
            
            # 更新未读通知计数
            unread_count = request.user.notifications.filter(is_read=False).count()
            
            print("通知标记为已读成功")
            return JsonResponse({
                'success': True,
                'unread_count': unread_count
            })
        except Exception as e:
            print(f"\n错误详情: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    print("\n请求方法不支持")
    return JsonResponse({'success': False, 'error': '只支持POST请求'}, status=400)

@login_required
def pin_conversation(request, user_id):
    """置顶对话"""
    if request.method == 'POST':
        try:
            other_user = get_object_or_404(User, id=user_id)
            
            # 获取或创建用户配置
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # 切换置顶状态
            if other_user in profile.pinned_conversations.all():
                profile.pinned_conversations.remove(other_user)
                is_pinned = False
            else:
                profile.pinned_conversations.add(other_user)
                is_pinned = True
            
            return JsonResponse({
                'success': True,
                'is_pinned': is_pinned
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': '只支持POST请求'
    }, status=400)

@login_required
def delete_conversation(request, user_id):
    """删除对话"""
    if request.method == 'POST':
        try:
            other_user = get_object_or_404(User, id=user_id)
            
            # 删除双方的所有私信
            deleted_count, _ = PrivateMessage.objects.filter(
                (Q(sender=request.user) & Q(recipient=other_user)) |
                (Q(sender=other_user) & Q(recipient=request.user))
            ).delete()
            
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': '只支持POST请求'
    }, status=400)

def search_users(request):
    """搜索用户视图函数"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '')
        if query:
            # 搜索用户名包含查询词的用户，限制返回前10个结果
            users = User.objects.filter(username__icontains=query)[:10]
            # 准备用户数据
            user_data = []
            for user in users:
                user_info = {
                    'id': user.id,
                    'username': user.username
                }
                # 尝试获取用户头像
                try:
                    if hasattr(user, 'userprofile') and user.userprofile.avatar:
                        user_info['avatar'] = user.userprofile.avatar.url
                    else:
                        user_info['avatar'] = None
                except:
                    user_info['avatar'] = None
                    
                user_data.append(user_info)
            
            return JsonResponse({'users': user_data})
    
    return JsonResponse({'users': []})


def load_more_comments(request):
    try:
        offset = int(request.GET.get('offset', 0))
        limit = 5  # 每次加载5条评论
        photo_id = request.GET.get('photo_id')
        photo = get_object_or_404(Photo, pk=photo_id)
        
        # 1. 先查询所有顶级评论（未分页）
        all_top_comments = photo.comments.filter(parent=None).order_by('-created_at')
        
        # 2. 分页（只处理当前页需要展示的评论）
        paginator = Paginator(all_top_comments, limit)
        page = (offset // limit) + 1
        page_comments = paginator.get_page(page)  # 当前页评论（仅这部分需要处理）
        
        # 3. 定义递归函数处理回复和点赞状态
        def set_liked_status(comment, user):
            # 设置当前评论的点赞状态
            comment.is_liked = comment.comment_likes.filter(user=user).exists()
            # 获取直接回复并排序
            replies = comment.replies.all().order_by('-created_at')
            # 递归处理每条回复（子回复的回复）
            for reply in replies:
                set_liked_status(reply, user)
            # 绑定处理好的回复到当前评论
            comment.processed_replies = replies
        
        # 4. 仅处理当前页的评论（包含其所有嵌套回复）
        for comment in page_comments:
            set_liked_status(comment, request.user)
        
        # 5. 构建返回数据（渲染模板）
        comments_data = []
        for comment in page_comments:
            comments_data.append({
                'html': render_to_string(
                    'photos/comment_item.html', 
                    {'comment': comment, 'user': request.user},
                    request=request
                )
            })
        
        return JsonResponse({
            'comments': comments_data,
            'has_more': page_comments.has_next()  # 补充是否有更多页的标识（前端分页需要）
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
