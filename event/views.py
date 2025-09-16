from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Event, EventModel, EventSession, EventRegistration
from .forms import EventForm
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db import transaction
import os

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
    event = get_object_or_404(
        Event.objects.select_related('created_by', 'location_user', 'location_user__userprofile')
        .prefetch_related('models__model_user__userprofile'), 
        pk=pk, 
        approved=True
    )
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
            
            # 处理地理位置信息
            if 'location_poi' in request.POST:
                event.location_poi = request.POST['location_poi']
            
            # 处理场地提供者用户ID
            location_user_id = request.POST.get('location_user')
            if location_user_id:
                try:
                    event.location_user = User.objects.get(id=location_user_id)
                except (User.DoesNotExist, ValueError):
                    event.location_user = None
            else:
                event.location_user = None
            
            # 保存活动对象
            event.save()
            
            # 处理模特信息
            model_count = 0
            for key in request.POST.keys():
                if key.startswith('model_name_'):
                    model_count += 1
                    model_name = request.POST.get(f'model_name_{model_count}')
                    model_fee = request.POST.get(f'model_fee_{model_count}')
                    model_vip_fee = request.POST.get(f'model_vip_fee_{model_count}')
                    
                    if model_name and model_fee:
                        # 创建模特
                        event_model = EventModel(
                            event=event,
                            name=model_name,
                            fee=model_fee
                        )
                        
                        # 设置VIP价格（如果提供）
                        if model_vip_fee:
                            event_model.vip_fee = model_vip_fee
                        
                        # 处理模特用户ID
                        model_user_id = request.POST.get(f'model_user_{model_count}')
                        if model_user_id:
                            try:
                                event_model.model_user = User.objects.get(id=model_user_id)
                            except (User.DoesNotExist, ValueError):
                                event_model.model_user = None
                        else:
                            event_model.model_user = None
                        
                        event_model.save()
                        
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
                        # 获取该模特的photographer_count
                        model_photographer_count = request.POST.get(f'model_photographer_count_{model_count}', 1)
                        
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
                                        end_time=end_time,
                                        photographer_count=model_photographer_count
                                    )
            
            messages.success(request, '活动创建成功，等待管理员审核！')
            return redirect('event:event_list')
    else:
        form = EventForm()
    
    return render(request, 'event/create_event.html', {
        'form': form,
        'ak': '46xD48lIm4oyiWq1RaKyxhr2ZhkZiCWg'
    })


@login_required
@require_POST
def register_session(request, session_id):
    """报名参加活动场次"""
    session = get_object_or_404(EventSession, id=session_id)
    
    # 检查是否还有名额
    if session.remaining_spots() <= 0:
        return JsonResponse({
            'success': False,
            'message': '该场次报名名额已满'
        })
    
    # 检查用户是否已经报名
    if EventRegistration.objects.filter(session=session, user=request.user).exists():
        return JsonResponse({
            'success': False,
            'message': '您已经报名参加该场次'
        })
    
    # 创建报名记录
    try:
        with transaction.atomic():
            EventRegistration.objects.create(session=session, user=request.user)
            return JsonResponse({
                'success': True,
                'message': '报名成功',
                'remaining_spots': session.remaining_spots()
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': '报名失败，请稍后重试'
        })
