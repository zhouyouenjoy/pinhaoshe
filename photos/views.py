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
# 从当前应用的models模块导入Photo、Album和UserProfile模型
from .models import Photo, Album, UserProfile, Comment, Like, Favorite, ViewHistory, Follow
# 导入PIL Image模块用于处理图片
from PIL import Image
# 导入BytesIO用于处理内存中的二进制数据
from io import BytesIO

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
        widget=forms.TextInput(attrs={'type': 'file', 'multiple': True, 'class': 'form-control'}),
        label='图片',
        required=False
    )
    
    def clean_images(self):
        files = self.files.getlist('images')
        if not files:
            raise forms.ValidationError("请至少上传一张图片")
        return files


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
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            # 获取表单数据
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            avatar = form.cleaned_data.get('avatar')
            
            # 创建新用户
            user = User.objects.create_user(username=username, password=password)
            
            # 创建用户资料
            user_profile = UserProfile.objects.create(user=user, email=email)
            
            # 如果上传了头像，则保存
            if avatar:
                user_profile.avatar = avatar
                user_profile.save()
            
            messages.success(request, '注册成功！现在可以登录了。')
            return redirect('login')
        else:
            # 表单验证失败，显示错误信息
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'photos/register.html', {'form': form})
    else:
        # GET请求，显示注册表单
        form = UserRegisterForm()
        return render(request, 'photos/register.html', {'form': form})


@login_required
def upload_photo(request):
    """上传照片"""
    # 判断请求方法是POST还是GET
    if request.method == 'POST':
        # 如果是POST请求，创建包含POST数据和文件数据的表单实例
        form = PhotoForm(request.POST, request.FILES)
        # 验证表单数据是否有效
        if form.is_valid():
            # 获取上传的文件列表
            images = request.FILES.getlist('images')
            
            # 检查上传文件数量
            if len(images) > 9:
                messages.error(request, '最多只能上传9张照片！')
                return render(request, 'photos/upload.html', {'form': form})
            
            if len(images) == 0:
                messages.error(request, '请至少选择一张照片！')
                return render(request, 'photos/upload.html', {'form': form})
            
            # 获取表单数据
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            display_image_index = form.cleaned_data.get('display_image_index')
            
            # 创建相册
            album = Album(
                title=title,
                description=description,
                uploaded_by=request.user
            )
            album.save()
            
            # 保存每张照片
            photo_objects = []
            for i, image in enumerate(images):
                photo = Photo(
                    title=title,  # 使用相册标题作为每张照片的标题
                    description=description,
                    image=image,
                    uploaded_by=request.user,
                    album=album
                )
                
                # 如果指定了展示图索引且匹配当前图片索引，则设置为展示图
                if display_image_index is not None and int(display_image_index) == i:
                    # 先保存照片以获取文件路径
                    photo.save()
                    
                    # 创建展示图
                    image_obj = Image.open(image)
                    # 转换RGBA为RGB以确保JPEG兼容性
                    if image_obj.mode in ('RGBA', 'LA') or (image_obj.mode == 'P' and 'transparency' in image_obj.info):
                        image_obj = image_obj.convert('RGB')
                    
                    # 调整大小为300x300
                    output_size = (300, 300)
                    image_obj.thumbnail(output_size)
                    
                    # 保存到内存缓冲区
                    buffer = BytesIO()
                    image_obj.save(buffer, format='JPEG')
                    buffer.seek(0)
                    
                    # 保存展示图
                    photo.display_image.save(
                        f"display_{image.name}",
                        BytesIO(buffer.read()),
                        save=True
                    )
                else:
                    photo.save()
                
                photo_objects.append(photo)
            
            # 如果没有指定展示图，则默认使用第一张作为展示图
            if display_image_index is None and photo_objects:
                first_photo = photo_objects[0]
                first_image = Image.open(first_photo.image)
                if first_image.mode in ('RGBA', 'LA') or (first_image.mode == 'P' and 'transparency' in first_image.info):
                    first_image = first_image.convert('RGB')
                
                output_size = (300, 300)
                first_image.thumbnail(output_size)
                
                buffer = BytesIO()
                first_image.save(buffer, format='JPEG')
                buffer.seek(0)
                
                first_photo.display_image.save(
                    f"display_{first_photo.image.name}",
                    BytesIO(buffer.read()),
                    save=True
                )
            
            # 添加成功消息提示
            messages.success(request, f'成功上传{len(images)}张照片，等待管理员审核！')
            # 重定向到照片画廊页面
            return redirect('gallery')
    else:
        # 如果是GET请求，创建一个空的表单实例
        form = PhotoForm()
    
    # 渲染上传照片页面，并传递表单变量
    return render(request, 'photos/upload.html', {'form': form})


# Add new photo_detail view function
def photo_detail(request, pk):
    """Display detailed information for a specific photo with carousel of album"""
    photo = get_object_or_404(Photo, pk=pk)
    # 获取该照片所属相册的所有照片
    if photo.album:
        photos = Photo.objects.filter(album=photo.album).order_by('id')
    else:
        photos = [photo]
    
    # 获取评论
    comments = photo.comments.all().order_by('-created_at')
    
    # 检查当前用户是否已点赞、收藏或关注上传者
    is_liked = False
    is_favorited = False
    is_following = False
    if request.user.is_authenticated:
        is_liked = photo.likes.filter(user=request.user).exists()
        is_favorited = photo.favorites.filter(user=request.user).exists()
        is_following = Follow.objects.filter(follower=request.user, followed=photo.uploaded_by).exists()
        
        # 添加浏览历史
        view_history, created = ViewHistory.objects.get_or_create(
            user=request.user,
            photo=photo
        )
        if not created:
            view_history.save()  # 更新浏览时间
    
    # 获取点赞和收藏数量
    like_count = photo.likes.count()
    favorite_count = photo.favorites.count()
    
    return render(request, 'photos/detail.html', {
        'photo': photo,
        'photos': photos,
        'comments': comments,
        'is_liked': is_liked,
        'is_favorited': is_favorited,
        'like_count': like_count,
        'favorite_count': favorite_count
    })


def album_detail(request, pk):
    """Display all photos in a specific album"""
    album = get_object_or_404(Album, pk=pk)
    photos = album.photo_set.all()
    return render(request, 'photos/album_detail.html', {'album': album, 'photos': photos})
# Add new my_photos view function
@login_required
def my_photos(request):
    """Display photos uploaded by the current user"""
    photos = Photo.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    return render(request, 'photos/my_photos.html', {'photos': photos})


@login_required
def liked_photos(request):
    """显示当前用户点赞的所有照片"""
    likes = Like.objects.filter(user=request.user).select_related('photo')
    return render(request, 'photos/liked_photos.html', {'likes': likes})


@login_required
def favorited_photos(request):
    """显示当前用户收藏的所有照片"""
    favorites = Favorite.objects.filter(user=request.user).select_related('photo')
    return render(request, 'photos/favorited_photos.html', {'favorites': favorites})


@login_required
def viewed_photos(request):
    """显示当前用户浏览历史"""
    view_history = ViewHistory.objects.filter(user=request.user).select_related('photo')
    return render(request, 'photos/viewed_photos.html', {'view_history': view_history})


def user_albums(request, user_id):
    """显示特定用户上传的所有相册"""
    target_user = get_object_or_404(User, pk=user_id)
    # 获取该用户上传的所有相册
    albums = Album.objects.filter(uploaded_by=target_user).order_by('-uploaded_at')
    return render(request, 'photos/user_albums.html', {'target_user': target_user, 'albums': albums})


def my_info(request):
    """用户信息页面，包含用户信息修改功能"""
    # 获取目标用户（默认为当前用户）
    user_id = request.GET.get('user_id')
    target_user = get_object_or_404(User, pk=user_id) if user_id else request.user
    
    # 获取或创建用户资料
    user_profile, created = UserProfile.objects.get_or_create(user=target_user)
    
    # 获取用户的点赞、收藏和浏览历史（仅当前用户可见）
    likes = []
    favorites = []
    view_history = []
    
    # 获取关注和粉丝数量
    following_count = target_user.following.count()
    followers_count = target_user.followers.count()
    
    # 检查是否已关注该用户
    is_following = False
    if request.user.is_authenticated and request.user != target_user:
        is_following = Follow.objects.filter(follower=request.user, followed=target_user).exists()
    
    if request.user == target_user:
        likes = Like.objects.filter(user=target_user).select_related('photo')
        favorites = Favorite.objects.filter(user=target_user).select_related('photo')
        view_history = ViewHistory.objects.filter(user=target_user)[:10]  # 最近10条浏览记录
    
    if request.method == 'POST' and request.user == target_user:
        form = UserSpaceForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # 获取表单数据
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            avatar = form.cleaned_data.get('avatar')
            
            # 检查用户名是否已存在（且不是当前用户）
            if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
                messages.error(request, '用户名已存在！')
            else:
                # 更新用户名（限制一年修改2次）
                if username != request.user.username:
                    # 这里应该添加一年修改2次的限制逻辑
                    # 为简化实现，我们暂时不添加这个限制
                    request.user.username = username
                    request.user.save()
                    messages.success(request, '用户名已更新！')
                
                # 更新邮箱
                if hasattr(request.user, 'userprofile'):
                    request.user.userprofile.email = email
                    # 如果上传了新头像，则更新
                    if avatar:
                        request.user.userprofile.avatar = avatar
                    request.user.userprofile.save()
                    messages.success(request, '个人信息已更新！')
                else:
                    # 创建用户资料
                    UserProfile.objects.create(user=request.user, email=email, avatar=avatar)
                    messages.success(request, '个人信息已更新！')
            
            return redirect('my_info')
    else:
        if request.user == target_user:
            form = UserSpaceForm(user=request.user)
        else:
            form = None
    
    return render(request, 'photos/my_space.html', {
        'target_user': target_user,
        'form': form,
        'likes': likes,
        'favorites': favorites,
        'view_history': view_history,
        'following_count': following_count,
        'followers_count': followers_count,
        'is_following': is_following
    })


@login_required
def delete_photo(request, photo_id):
    """删除照片功能"""
    photo = get_object_or_404(Photo, pk=photo_id, uploaded_by=request.user)
    
    if request.method == 'POST':
        photo.delete()
        messages.success(request, '照片已删除！')
        return redirect('my_photos')
    
    return render(request, 'photos/delete_photo.html', {'photo': photo})


@login_required
def add_comment(request, photo_id):
    """添加评论"""
    photo = get_object_or_404(Photo, pk=photo_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                photo=photo,
                user=request.user,
                content=content
            )
            messages.success(request, '评论已添加！')
        else:
            messages.error(request, '评论内容不能为空！')
    
    return redirect('photo_detail', pk=photo_id)


@login_required
def delete_comment(request, comment_id):
    """删除评论"""
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # 检查用户是否有权限删除评论（评论者本人或照片上传者）
    if request.user != comment.user and request.user != comment.photo.uploaded_by:
        messages.error(request, '您没有权限删除此评论！')
        return redirect('photo_detail', pk=comment.photo.pk)
    
    photo_pk = comment.photo.pk
    comment.delete()
    messages.success(request, '评论已删除！')
    return redirect('photo_detail', pk=photo_pk)


@login_required
def toggle_like(request, photo_id):
    """切换点赞状态"""
    photo = get_object_or_404(Photo, pk=photo_id)
    
    like, created = Like.objects.get_or_create(
        photo=photo,
        user=request.user
    )
    
    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        like_count = photo.likes.count()
        return JsonResponse({
            'is_liked': is_liked,
            'like_count': like_count
        })
    
    return redirect('photo_detail', pk=photo_id)


@login_required
def toggle_favorite(request, photo_id):
    """切换收藏状态"""
    photo = get_object_or_404(Photo, pk=photo_id)
    
    favorite, created = Favorite.objects.get_or_create(
        photo=photo,
        user=request.user
    )
    
    if not created:
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        favorite_count = photo.favorites.count()
        return JsonResponse({
            'is_favorited': is_favorited,
            'favorite_count': favorite_count
        })
    
    return redirect('photo_detail', pk=photo_id)


@login_required
def toggle_follow(request, user_id):
    """切换关注状态"""
    target_user = get_object_or_404(User, pk=user_id)
    
    # 不能关注自己
    if request.user == target_user:
        return JsonResponse({'error': '不能关注自己'}, status=400)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        followed=target_user
    )
    
    if not created:
        follow.delete()
        is_following = False
    else:
        is_following = True
    
    # 获取最新的关注和粉丝数量
    following_count = target_user.following.count()
    followers_count = target_user.followers.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'is_following': is_following,
            'following_count': following_count,
            'followers_count': followers_count
        })
    
    return redirect('my_info')