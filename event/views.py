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
from django.utils import timezone
import os

def event_list(request):
    """摄影活动列表页面"""
    
    # 处理AJAX请求（懒加载）
    page = int(request.GET.get('page', 1))
    events = Event.objects.filter(approved=True).order_by('-created_at').prefetch_related(
        'models__sessions'
    )
    
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
        .prefetch_related('models__model_user__userprofile', 'models__sessions'), 
        pk=pk, 
        approved=True
    )
    
    # 获取当前用户已报名的场次（如果用户已登录）
    user_registrations = set()
    if request.user.is_authenticated:
        registrations = EventRegistration.objects.filter(
            session__model__event=event,
            user=request.user
        ).select_related('session')
        user_registrations = {reg.session.id for reg in registrations}
    
    return render(request, 'event/event_detail.html', {
        'event': event,
        'user_registrations': user_registrations
    })


def model_album(request, model_id):
    """获取模特相册照片"""
    try:
        # 获取模特对象
        model = get_object_or_404(EventModel, id=model_id)
        
        # 获取模特关联用户的照片
        photos = []
        if model.model_user:
            # 获取用户上传的照片，按上传时间倒序排列
            user_photos = model.model_user.photo_set.filter(approved=True).order_by('-uploaded_at')
            for photo in user_photos:
                photos.append({
                    'id': photo.id,
                    'title': photo.title,
                    'image': photo.image.url if photo.image else '',
                    'description': photo.description
                })
        
        return JsonResponse({
            'success': True,
            'model_name': model.name,
            'photos': photos
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def create_event(request, event_id=None):
    """创建或编辑摄影活动"""
    # 检查是否是编辑模式
    is_edit = event_id is not None
    if is_edit:
        event = get_object_or_404(Event, pk=event_id, created_by=request.user)
    else:
        event = None
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            # 默认设置为已审核通过状态
            event.approved = True
            
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
            
            # 如果是编辑模式，处理模特信息的更新
            if is_edit:
                # 处理现有模特的更新
                for model in event.models.all():
                    # 检查是否有删除图片的标记
                    if request.POST.get(f'delete_model_images_{model.id}'):
                        model.model_images = None
                    if request.POST.get(f'delete_outfit_images_{model.id}'):
                        model.outfit_images = None
                    if request.POST.get(f'delete_scene_images_{model.id}'):
                        model.scene_images = None
                    
                    # 处理新上传的图片
                    model_images = request.FILES.getlist(f'model_images_{model.id}')
                    if model_images:
                        model.model_images = model_images[0]
                    
                    outfit_images = request.FILES.getlist(f'outfit_images_{model.id}')
                    if outfit_images:
                        model.outfit_images = outfit_images[0]
                    
                    scene_images = request.FILES.getlist(f'scene_images_{model.id}')
                    if scene_images:
                        model.scene_images = scene_images[0]
                    
                    # 更新其他字段
                    model_name_key = f'model_name_{model.id}'
                    model_fee_key = f'model_fee_{model.id}'
                    model_vip_fee_key = f'model_vip_fee_{model.id}'
                    model_photographer_count_key = f'model_photographer_count_{model.id}'
                    model_user_key = f'model_user_{model.id}'
                    
                    if model_name_key in request.POST:
                        model.name = request.POST[model_name_key]
                    
                    if model_fee_key in request.POST:
                        model.fee = request.POST[model_fee_key]
                    
                    if model_vip_fee_key in request.POST:
                        vip_fee = request.POST[model_vip_fee_key]
                        model.vip_fee = vip_fee if vip_fee else None
                    
                    if model_user_key in request.POST:
                        model_user_id = request.POST[model_user_key]
                        if model_user_id:
                            try:
                                model.model_user = User.objects.get(id=model_user_id)
                            except (User.DoesNotExist, ValueError):
                                model.model_user = None
                        else:
                            model.model_user = None
                    
                    model.save()
            
            # 如果是创建模式，处理新模特的创建
            if not is_edit:
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
            
            messages.success(request, '活动创建成功！' if not is_edit else '活动更新成功！')
            return redirect('event:event_list')
    else:
        form = EventForm(instance=event)
    
    # 获取现有模特信息（用于编辑模式）
    existing_models = []
    if is_edit and event:
        existing_models = EventModel.objects.filter(event=event).prefetch_related('sessions')
    
    return render(request, 'event/create_event.html', {
        'form': form,
        'ak': '46xD48lIm4oyiWq1RaKyxhr2ZhkZiCWg',
        'is_edit': is_edit,
        'event': event,
        'existing_models': existing_models
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

@login_required
def my_events(request):
    """我的活动页面 - 展示用户发布的活动和参与的活动"""
    # 获取用户发布的活动
    hosted_events = Event.objects.filter(created_by=request.user).order_by('-created_at')
    
    # 获取用户参与的活动（通过报名记录）
    participated_events = Event.objects.filter(
        models__sessions__registrations__user=request.user
    ).distinct().order_by('-event_time')
    
    return render(request, 'event/my_events.html', {
        'hosted_events': hosted_events,
        'participated_events': participated_events
    })


@login_required
def event_registrations(request, event_id):
    """查看活动报名名单"""
    # 确保只有活动创建者可以查看报名名单
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)
    
    # 获取所有报名该活动的用户
    registrations = EventRegistration.objects.filter(
        session__model__event=event
    ).select_related(
        'user', 
        'user__userprofile',
        'session',
        'session__model'
    ).order_by('session__model__name', 'session__title', 'registered_at')
    
    # 按模特分组注册信息
    model_registrations = {}
    for registration in registrations:
        model = registration.session.model
        if model not in model_registrations:
            model_registrations[model] = []
        model_registrations[model].append(registration)
    
    # 获取活动场次总数
    sessions_count = EventSession.objects.filter(model__event=event).count()
    
    # 确保所有模特都包含在model_registrations中，即使没有报名用户
    all_models = EventModel.objects.filter(event=event)
    for model in all_models:
        if model not in model_registrations:
            model_registrations[model] = []
    
    # 为每个模特预处理场次信息
    model_sessions_info = {}
    for model in all_models:
        model_sessions_info[model.id] = []
        # 获取该模特的所有场次
        sessions = model.sessions.all()
        # 获取该模特的报名信息（如果有的话）
        model_regs = model_registrations.get(model, [])
        # 按场次分组报名信息
        session_registrations = {}
        for reg in model_regs:
            session_id = reg.session.id
            if session_id not in session_registrations:
                session_registrations[session_id] = []
            session_registrations[session_id].append(reg)
        
        # 为每个场次准备显示信息
        for session in sessions:
            session_info = {
                'session': session,
                'registrations': session_registrations.get(session.id, [])
            }
            model_sessions_info[model.id].append(session_info)
    
    return render(request, 'event/event_registrations.html', {
        'event': event,
        'registrations': registrations,
        'model_registrations': model_registrations,
        'model_sessions_info': model_sessions_info,
        'sessions_count': sessions_count
    })