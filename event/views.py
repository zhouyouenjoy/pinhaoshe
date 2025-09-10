from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Event, EventModel, EventSession
from .forms import EventForm

def event_list(request):
    """摄影活动列表页面"""
    
        # 处理AJAX请求（懒加载）
    page = int(request.GET.get('page', 1))
    events = Event.objects.filter(approved=True).order_by('-created_at')
    
    paginator = Paginator(events, 3)  # 每页6个活动
    events_page = paginator.get_page(page)
    if page == 1:
       # 前端要求完整页面
        
        
        return render(request, 'event/event_list.html', {
            'events': events_page
        })
          
    # 渲染活动列表内容模板
    html = render(request, 'event/event_list_content.html', {
        'events': events_page
    }).content.decode('utf-8')
    
    # 返回JSON响应
    return JsonResponse({
        'html': html,
        'has_next': events_page.has_next(),
        'next_page': events_page.next_page_number() if events_page.has_next() else None
    })
    
    

def event_detail(request, pk):
    """摄影活动详情页面"""
    event = get_object_or_404(Event, pk=pk, approved=True)
    return render(request, 'event/event_detail.html', {
        'event': event
    })

@login_required
def create_event(request):
    """创建摄影活动"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            # 默认需要审核
            event.approved = False
            # 先保存活动对象
            event.save()
            
            # 处理模特信息
            model_count = 0
            for key in request.POST.keys():
                if key.startswith('model_name_'):
                    model_count += 1
                    model_name = request.POST.get(f'model_name_{model_count}')
                    model_fee = request.POST.get(f'model_fee_{model_count}')
                    
                    if model_name and model_fee:
                        # 创建模特
                        event_model = EventModel.objects.create(
                            event=event,
                            name=model_name,
                            fee=model_fee
                        )
                        
                        # 处理模特照片上传
                        model_images = request.FILES.getlist(f'model_images_{model_count}')
                        if model_images:
                            # 保存第一张图片到model_images字段
                            event_model.model_images = model_images[0]
                        
                        # 处理模特服装图片上传
                        outfit_images = request.FILES.getlist(f'outfit_images_{model_count}')
                        if outfit_images:
                            # 保存第一张图片到outfit_images字段
                            event_model.outfit_images = outfit_images[0]
                        
                        # 处理拍摄场景图片上传
                        scene_images = request.FILES.getlist(f'scene_images_{model_count}')
                        if scene_images:
                            # 保存第一张图片到scene_images字段
                            event_model.scene_images = scene_images[0]
                        
                        event_model.save()
                        
                        # 处理场次信息
                        session_count = 0
                        for session_key in request.POST.keys():
                            if session_key.startswith(f'start_time_{model_count}_'):
                                session_count += 1
                                start_time = request.POST.get(f'start_time_{model_count}_{session_count}')
                                end_time = request.POST.get(f'end_time_{model_count}_{session_count}')
                                
                                if start_time and end_time:
                                    EventSession.objects.create(
                                        model=event_model,
                                        title=f'场次 {session_count}',
                                        start_time=start_time,
                                        end_time=end_time
                                    )
            
            messages.success(request, '活动创建成功，等待管理员审核！')
            return redirect('event:event_list')
    else:
        form = EventForm()
    
    return render(request, 'event/create_event.html', {
        'form': form
    })

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
                    from photos.models import UserProfile
                    user_profile = UserProfile.objects.get(user=user)
                    if user_profile.avatar:
                        user_info['avatar'] = user_profile.avatar.url
                    else:
                        user_info['avatar'] = None
                except:
                    user_info['avatar'] = None
                    
                user_data.append(user_info)
            
            return JsonResponse({'users': user_data})
    
    return JsonResponse({'users': []})