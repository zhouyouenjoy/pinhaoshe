from django.db.models import Subquery, OuterRef, Max

def gallery(request):
    """展示所有已批准的照片"""
    # 获取每个标题和用户组的最新展示图
    latest_display_photos = Photo.objects.filter(
        approved=True,
        is_display_image=True,
        title=OuterRef('title'),
        uploaded_by=OuterRef('uploaded_by')
    ).values('title', 'uploaded_by').annotate(
        max_uploaded_at=Max('uploaded_at')
    ).values('max_uploaded_at')
    
    # 查询最终展示的照片
    photos = Photo.objects.filter(
        approved=True,
        is_display_image=True,
        uploaded_at__in=Subquery(latest_display_photos)
    ).order_by('-uploaded_at')
    
    # 渲染photos/gallery.html模板，并传递photos变量
    return render(request, 'photos/gallery.html', {'photos': photos})


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
            
            # 创建相册
            album = Album(
                title=title,
                description=description,
                uploaded_by=request.user
            )
            album.save()
            
            # 保存每张照片
            for index, image in enumerate(images):
                photo = Photo(
                    title=title,  # 使用相册标题作为每张照片的标题
                    description=description,
                    image=image,
                    uploaded_by=request.user,
                    album=album,
                    # 设置第一张图片为展示图
                    is_display_image=(index == 0)
                )
                photo.save()
            
            # 添加成功消息提示
            messages.success(request, f'成功上传{len(images)}张照片，等待管理员审核！')
            # 重定向到照片画廊页面
            return redirect('gallery')