# 从django.shortcuts导入常用函数
from django.shortcuts import render, redirect, get_object_or_404
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
from django.core.paginator import Paginator
# 从当前应用的models模块导入模型
from .models import Photo, Album, UserProfile, Comment, Like, Favorite, ViewHistory, Follow, CommentLike, PrivateMessage
# 导入PIL Image模块用于处理图片
from PIL import Image
# 导入BytesIO用于处理内存中的二进制数据
from io import BytesIO
# 导入json模块用于处理JSON数据
import json

# 导入表单
from .forms import PhotoForm, UserRegisterForm, UserSpaceForm

# 导入get_current_site用于获取当前站点信息
from django.contrib.sites.shortcuts import get_current_site

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


def gallery(request):
    """展示所有已批准的相册，每组只显示第一张照片"""
    # 获取所有已批准的相册，并按上传时间倒序排列
    albums = Album.objects.filter(approved=True).order_by('-uploaded_at')
    # 渲染photos/gallery.html模板，并传递albums变量
    return render(request, 'photos/gallery.html', {'albums': albums})


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
        form = UserRegisterForm(request.POST)
        # 验证表单数据是否有效
        if form.is_valid():
            # 保存用户信息（但不立即提交到数据库）
            user = form.save(commit=False)
            # 设置用户密码
            user.set_password(form.cleaned_data['password1'])
            # 保存用户到数据库
            user.save()
            # 创建用户个人资料
            UserProfile.objects.create(user=user)
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
            
            # 遍历所有上传的图片
            for image in images:
                # 为每张图片创建Photo对象
                photo = Photo(
                    title=title,
                    description=description,
                    image=image,
                    uploaded_by=request.user
                )
                photo.save()
            
            # 添加成功消息
            messages.success(request, '照片上传成功！')
            # 重定向到首页
            return redirect('gallery')
    else:
        form = PhotoForm()
    return render(request, 'photos/upload.html', {'form': form})


def photo_detail(request, pk):
    """照片详情视图"""
    # 获取指定ID的照片对象，如果不存在则返回404错误
    photo = get_object_or_404(Photo, pk=pk)
    
    # 如果用户已登录，记录浏览历史
    if request.user.is_authenticated:
        view_history, created = ViewHistory.objects.get_or_create(
            user=request.user,
            photo=photo
        )
        if not created:
            # 如果记录已存在，更新浏览时间
            view_history.save()  # 会自动更新viewed_at字段
    
    # 获取照片的所有评论，并按创建时间倒序排列
    comments = photo.comments.filter(parent=None).order_by('-created_at')
    
    # 分页处理，每页显示5条评论
    paginator = Paginator(comments, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 检查用户是否已点赞、收藏该照片
    user_liked = False
    user_favorited = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, photo=photo).exists()
        user_favorited = Favorite.objects.filter(user=request.user, photo=photo).exists()
    
    # 准备评论用户的关注状态
    comment_users_following = {}
    if request.user.is_authenticated:
        # 获取评论用户列表
        comment_users = [comment.user for comment in comments]
        # 查询当前用户对这些用户的关注状态
        follows = Follow.objects.filter(
            follower=request.user,
            followed__in=comment_users
        ).values_list('followed_id', flat=True)
        
        # 构建关注状态字典
        comment_users_following = {user_id: True for user_id in follows}
    
    # 渲染照片详情页面模板，并传递相关变量
    context = {
        'photo': photo,
        'comments': page_obj,
        'user_liked': user_liked,
        'user_favorited': user_favorited,
        'comment_users_following': comment_users_following,
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
        return redirect('user_albums', user_id=request.user.id)
    
    # 如果是POST请求，执行删除操作
    if request.method == 'POST':
        album.delete()
        # 添加成功消息
        messages.success(request, '相册删除成功。')
        return redirect('user_albums', user_id=request.user.id)
    
    # 如果是GET请求，显示确认页面
    return render(request, 'photos/delete_album.html', {'album': album})


@login_required
def user_albums(request, user_id):
    """用户相册视图"""
    # 获取指定用户
    target_user = get_object_or_404(User, id=user_id)
    # 获取该用户创建的所有相册
    albums = Album.objects.filter(uploaded_by=target_user).order_by('-uploaded_at')
    
    # 检查当前用户是否关注了目标用户
    is_following = False
    if request.user.is_authenticated and request.user != target_user:
        is_following = Follow.objects.filter(follower=request.user, followed=target_user).exists()
    
    # 统计关注数和粉丝数
    following_count = target_user.following.count()
    followers_count = target_user.followers.count()
    
    # 渲染用户相册页面模板，并传递相关变量
    return render(request, 'photos/user_albums.html', {
        'target_user': target_user,
        'albums': albums,
        'is_following': is_following,
        'following_count': following_count,
        'followers_count': followers_count,
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
    likes = Like.objects.filter(user=target_user).select_related('photo') if target_user == request.user else Like.objects.none()
    favorites = Favorite.objects.filter(user=target_user).select_related('photo') if target_user == request.user else Favorite.objects.none()
    view_history = ViewHistory.objects.filter(user=target_user)[:8] if target_user == request.user else []
    
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
            return redirect('my_info_with_id', user_id=target_user.id)
    else:
        # 初始化表单
        form = UserSpaceForm(instance=user_profile, initial={
            'username': target_user.username,
            'email': target_user.email
        }) if target_user == request.user else None
    
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


def following_albums(request):
    """关注用户的最新相册视图"""
    if request.user.is_authenticated:
        # 获取当前用户关注的用户
        following_users = User.objects.filter(followers__follower=request.user)
        # 获取关注用户创建的相册
        albums = Album.objects.filter(uploaded_by__in=following_users, approved=True).order_by('-uploaded_at')
    else:
        albums = Album.objects.none()
    
    return render(request, 'photos/following_albums.html', {'albums': albums})


def events(request):
    """摄影活动视图"""
    return render(request, 'photos/events.html')


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
        
        # 检查评论内容是否为空
        if content:
            # 创建评论
            Comment.objects.create(
                photo=photo,
                user=request.user,
                content=content
            )
            messages.success(request, '评论添加成功！')
        else:
            messages.error(request, '评论内容不能为空！')
        
        # 重定向到照片详情页面
        return redirect('photo_detail', pk=photo_id)
    
    # 如果不是POST请求，返回404错误
    return HttpResponse(status=404)


@login_required
def delete_comment(request, comment_id):
    """删除评论视图"""
    # 获取要删除的评论对象
    comment = get_object_or_404(Comment, id=comment_id)
    
    # 检查评论是否属于当前用户
    if comment.user != request.user:
        messages.error(request, '您没有权限删除这条评论。')
        return redirect('photo_detail', pk=comment.photo.id)
    
    # 获取照片ID用于重定向
    photo_id = comment.photo.id
    
    # 删除评论
    comment.delete()
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
        content = request.POST.get('content')
        
        # 检查回复内容是否为空
        if content:
            # 创建回复评论
            Comment.objects.create(
                photo=parent_comment.photo,
                user=request.user,
                content=content,
                parent=parent_comment
            )
            messages.success(request, '回复添加成功！')
        else:
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


def get_photo_comments(request, photo_id):
    """获取照片评论视图（用于局部刷新）"""
    # 获取照片对象
    photo = get_object_or_404(Photo, id=photo_id)
    # 获取照片的所有评论，并按创建时间倒序排列
    comments = photo.comments.filter(parent=None).order_by('-created_at')
    
    # 分页处理，每页显示5条评论
    paginator = Paginator(comments, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 准备评论用户的关注状态
    comment_users_following = {}
    if request.user.is_authenticated:
        # 获取评论用户列表
        comment_users = [comment.user for comment in comments]
        # 查询当前用户对这些用户的关注状态
        follows = Follow.objects.filter(
            follower=request.user,
            followed__in=comment_users
        ).values_list('followed_id', flat=True)
        
        # 构建关注状态字典
        comment_users_following = {user_id: True for user_id in follows}
    
    # 渲染评论部分模板，并传递相关变量
    return render(request, 'photos/comments_partial.html', {
        'comments': page_obj,
        'comment_users_following': comment_users_following,
    })


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
        return redirect('my_info_with_id', user_id=recipient_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        
        if content:
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
            return redirect('my_info_with_id', user_id=recipient_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '私信内容不能为空！'}, status=400)
            messages.error(request, '私信内容不能为空！')
    
    # 如果是AJAX请求且不是POST，返回错误
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': '无效请求'}, status=400)
        
    return render(request, 'photos/send_message.html', {
        'recipient': recipient
    })


# 私信列表视图
@login_required
def messages_list(request):
    """
    显示当前用户收到的私信列表，每个用户只显示最新的一条消息
    """
    # 获取收到的私信，按发送者分组，只取每个发送者的最新一条
    received_messages = PrivateMessage.objects.filter(recipient=request.user)
    latest_received = {}
    for message in received_messages:
        sender_id = message.sender.id
        if sender_id not in latest_received or message.sent_at > latest_received[sender_id].sent_at:
            latest_received[sender_id] = message
    
    # 获取发送的私信，按接收者分组，只取每个接收者的最新一条
    sent_messages = PrivateMessage.objects.filter(sender=request.user)
    latest_sent = {}
    for message in sent_messages:
        recipient_id = message.recipient.id
        if recipient_id not in latest_sent or message.sent_at > latest_sent[recipient_id].sent_at:
            latest_sent[recipient_id] = message
    
    return render(request, 'photos/messages_list.html', {
        'messages_received': latest_received.values(),
        'messages_sent': latest_sent.values()
    })


# 私信详情视图
@login_required
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
        messages_data.append({
            'id': msg.id,
            'content': msg.content.replace('\n', '<br>'),
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sender': msg.sender.username,
            'is_own': msg.sender == request.user,
            'is_read': msg.is_read
        })
    
    return JsonResponse({
        'messages': messages_data
    })
