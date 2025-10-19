from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Event, EventModel, EventSession, EventRegistration, RefundRequest
from .forms import EventForm
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import timedelta
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
    
    # 获取当前用户已报名且已支付的场次（如果用户已登录）- 排除已退款的
    user_registrations = set()
    if request.user.is_authenticated:
        registrations = EventRegistration.objects.filter(
            session__model__event=event,
            user=request.user,
            is_refunded=False,  # 排除已退款的报名
            is_paid=True  # 必须已支付
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
                # 收集所有提交的模特ID，用于确定哪些现有模特需要删除
                submitted_model_ids = set()
                
                # 处理现有模特的更新和新模特的创建
                for key in request.POST.keys():
                    if key.startswith('model_name_'):
                        # 提取模特编号（可能是ID或序号）
                        model_identifier = key.split('_')[-1]
                        
                        # 获取相关字段值
                        model_name = request.POST.get(f'model_name_{model_identifier}')
                        model_fee = request.POST.get(f'model_fee_{model_identifier}')
                        model_vip_fee = request.POST.get(f'model_vip_fee_{model_identifier}')
                        model_user_id = request.POST.get(f'model_user_{model_identifier}')
                        # 获取photographer_count字段值
                        model_photographer_count = request.POST.get(f'model_photographer_count_{model_identifier}', 1)
                        
                        if model_name and model_fee:
                            # 检查是否是现有模特的更新（model_identifier是数字且对应现有模特ID）
                            model = None
                            try:
                                model_id = int(model_identifier)
                                model = EventModel.objects.get(id=model_id, event=event)
                            except (ValueError, EventModel.DoesNotExist):
                                model = None
                            
                            # 如果是现有模特，更新它；否则创建新模特
                            if model:
                                # 更新现有模特
                                model.name = model_name
                                model.fee = model_fee
                                if model_vip_fee:
                                    model.vip_fee = model_vip_fee
                                else:
                                    model.vip_fee = None
                                
                                # 处理模特用户
                                if model_user_id:
                                    try:
                                        model.model_user = User.objects.get(id=model_user_id)
                                    except (User.DoesNotExist, ValueError):
                                        model.model_user = None
                                else:
                                    model.model_user = None
                                
                                # 处理图片删除标记
                                if request.POST.get(f'delete_model_images_{model.id}'):
                                    model.model_images = None
                                if request.POST.get(f'delete_outfit_images_{model.id}'):
                                    model.outfit_images = None
                                if request.POST.get(f'delete_scene_images_{model.id}'):
                                    model.scene_images = None
                                
                                # 处理新上传的图片
                                model_images = request.FILES.getlist(f'model_images_{model_identifier}')
                                if model_images:
                                    model.model_images = model_images[0]
                                
                                outfit_images = request.FILES.getlist(f'outfit_images_{model_identifier}')
                                if outfit_images:
                                    model.outfit_images = outfit_images[0]
                                
                                scene_images = request.FILES.getlist(f'scene_images_{model_identifier}')
                                if scene_images:
                                    model.scene_images = scene_images[0]
                                
                                model.save()
                                submitted_model_ids.add(model.id)
                                
                                # 更新模特场次的photographer_count
                                if model.sessions.exists():
                                    model.sessions.all().update(photographer_count=model_photographer_count)
                                
                                # 处理场次信息更新
                                session_count = 0
                                for session_key in request.POST.keys():
                                    if session_key.startswith(f'start_time_{model_identifier}_'):
                                        session_count += 1
                                        start_time = request.POST.get(f'start_time_{model_identifier}_{session_count}')
                                        end_time = request.POST.get(f'end_time_{model_identifier}_{session_count}')
                                        
                                        if start_time and end_time:
                                            # 查找或创建场次
                                            try:
                                                session = model.sessions.get(title=f'场次 {session_count}')
                                                session.start_time = start_time
                                                session.end_time = end_time
                                                session.save()
                                            except EventSession.DoesNotExist:
                                                # 如果场次不存在，则创建新场次
                                                EventSession.objects.create(
                                                    model=model,
                                                    title=f'场次 {session_count}',
                                                    start_time=start_time,
                                                    end_time=end_time,
                                                    photographer_count=model_photographer_count
                                                )
                            else:
                                # 创建新模特
                                model = EventModel(
                                    event=event,
                                    name=model_name,
                                    fee=model_fee
                                )
                                
                                if model_vip_fee:
                                    model.vip_fee = model_vip_fee
                                
                                # 处理模特用户
                                if model_user_id:
                                    try:
                                        model.model_user = User.objects.get(id=model_user_id)
                                    except (User.DoesNotExist, ValueError):
                                        model.model_user = None
                                else:
                                    model.model_user = None
                                
                                # 处理图片上传
                                model_images = request.FILES.getlist(f'model_images_{model_identifier}')
                                if model_images:
                                    model.model_images = model_images[0]
                                
                                outfit_images = request.FILES.getlist(f'outfit_images_{model_identifier}')
                                if outfit_images:
                                    model.outfit_images = outfit_images[0]
                                
                                scene_images = request.FILES.getlist(f'scene_images_{model_identifier}')
                                if scene_images:
                                    model.scene_images = scene_images[0]
                                
                                model.save()
                                submitted_model_ids.add(model.id)
                                
                                # 为新模特创建默认场次
                                EventSession.objects.create(
                                    model=model,
                                    title='场次 1',
                                    start_time='10:00',
                                    end_time='12:00',
                                    photographer_count=model_photographer_count  # 使用提交的photographer_count
                                )
                
                # 删除未提交的现有模特（用户删除的模特）
                existing_model_ids = set(event.models.values_list('id', flat=True))
                models_to_delete = existing_model_ids - submitted_model_ids
                if models_to_delete:
                    EventModel.objects.filter(id__in=models_to_delete).delete()
            
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
@transaction.atomic
def register_session(request, session_id):
    """报名参加活动场次"""
    # 使用select_for_update锁住session记录，防止并发超卖
    session = get_object_or_404(EventSession.objects.select_for_update(), id=session_id)
    
    # 检查是否还有名额
    if session.remaining_spots() <= 0:
        return JsonResponse({
            'success': False,
            'message': '该场次报名名额已满'
        })
    
    # 检查用户是否已经有待支付的报名
    pending_registration = session.get_pending_registration(request.user)
    if pending_registration:
        # 检查是否过期
        if pending_registration.is_pending_expired():
            # 如果已过期，取消该报名并释放名额
            pending_registration.is_refunded = True
            pending_registration.save()
            # 继续允许用户报名
        else:
            # 如果未过期，不允许重复报名
            return JsonResponse({
                'success': False,
                'message': '您已有待支付的报名，请先完成支付或等待超时'
            })
    
    # 检查用户是否已经报名（排除已退款的报名）
    existing_registration = EventRegistration.objects.filter(
        session=session, 
        user=request.user
    ).first()
    
    if existing_registration:
        # 如果存在报名记录且未退款，则不允许重复报名
        if not existing_registration.is_refunded:
            return JsonResponse({
                'success': False,
                'message': '您已经报名参加该场次'
            })
        else:
            # 如果是已退款的报名，允许重新报名（创建新记录）
            # 不再更新现有记录，而是创建一个全新的报名记录
            pass  # 继续执行下面的创建逻辑
    
    # 创建报名记录
    try:
        with transaction.atomic():
            registration = EventRegistration.objects.create(session=session, user=request.user)
            # 返回需要支付的信息，前端将重定向到支付页面
            return JsonResponse({
                'success': True,
                'message': '报名成功',
                'registration_id': registration.id,
                'remaining_spots': session.remaining_spots(),
                'redirect_to_payment': True,  # 标记需要重定向到支付页面
                'payment_url': f'/pay/create/{registration.id}/'  # 支付页面URL
            })
    except IntegrityError as e:
        return JsonResponse({
            'success': False,
            'message': '您已经报名参加该场次'
        })
    except Exception as e:
        # 记录详细的错误信息用于调试
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Registration failed for user {request.user.id} session {session.id}: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': f'报名失败，请稍后重试 ({str(e)[:50]})'
        })


@login_required
def my_events(request):
    """我的活动页面 - 展示用户发布的活动和参与的活动"""
    # 获取用户发布的活动
    hosted_events = Event.objects.filter(created_by=request.user).order_by('-created_at')
    
    # 获取用户参与的活动场次信息（详细信息）
    # 获取所有报名记录，包括已退款的，用于在模板中区分显示
    all_participated_registrations = EventRegistration.objects.filter(
        user=request.user
    ).select_related(
        'session__model__event',
        'session__model__model_user__userprofile',
        'session'
    ).order_by('-session__model__event__event_time')
    
    # 对参与的活动进行自定义排序：
    # 1. 未退款的活动优先
    # 2. 按活动状态排序：未开始 > 进行中 > 已结束
    # 3. 按活动时间排序
    def registration_sort_key(registration):
        event = registration.session.model.event
        
        # 计算活动状态: ongoing(进行中), ended(已结束), upcoming(待开始)
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        if event.event_time < now:
            # 活动时间已过，判断是否结束（假设活动持续4小时）
            if event.event_time + timedelta(hours=4) < now:
                status = 'ended'
            else:
                status = 'ongoing'
        else:
            status = 'upcoming'
        
        # 退款的活动排在最后
        if registration.is_refunded:
            return (1, 0, event.event_time)
        
        # 未退款的活动按状态排序：未开始(0) > 进行中(1) > 已结束(2)
        status_order = {'upcoming': 0, 'ongoing': 1, 'ended': 2}
        return (0, status_order.get(status, 2), event.event_time)
    
    all_participated_registrations = sorted(
        all_participated_registrations,
        key=registration_sort_key
    )
    
    # 获取用户的报名记录，用于退款申请
    user_registrations = EventRegistration.objects.filter(user=request.user).select_related(
        'session__model__event'
    )
    
    # 创建一个字典，将event_id映射到registration_id
    event_registration_map = {}
    for registration in user_registrations:
        event_id = registration.session.model.event.id
        event_registration_map[event_id] = registration.id
    
    return render(request, 'event/my_events.html', {
        'hosted_events': hosted_events,
        'all_participated_registrations': all_participated_registrations,  # 所有参与的活动场次详细信息
        'event_registration_map': event_registration_map
    })


@login_required
def event_registrations(request, event_id):
    """查看活动报名名单"""
    # 确保只有活动创建者可以查看报名名单
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)
    
    # 获取所有报名该活动的用户（排除已退款的）
    registrations = EventRegistration.objects.filter(
        session__model__event=event,
        is_refunded=False  # 排除已退款的报名
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


@login_required
def my_refund_requests(request):
    """查看我提交的退款申请"""
    refund_requests = RefundRequest.objects.filter(registration__user=request.user).select_related(
        'registration__session__model__event'
    )
    return render(request, 'event/my_refund_requests.html', {'refund_requests': refund_requests})


@login_required
def pending_refunds(request):
    """查看待处理的退款申请（活动发布者）"""
    # 获取作为活动创建者的待处理退款申请
    pending_refunds = RefundRequest.objects.filter(
        registration__session__model__event__created_by=request.user,
        status='pending'
    ).select_related(
        'registration__user',
        'registration__session__model__event',
        'registration__session__model',
        'registration__session'
    ).order_by('-created_at')
    
    # 如果是AJAX请求，或者明确要求JSON格式，返回JSON数据
    if (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
        request.GET.get('format') == 'json' or
        request.content_type == 'application/json'):
        refund_requests_data = []
        for refund in pending_refunds:
            # 计算退款百分比
            hours_before_event = (refund.registration.session.model.event.event_time - timezone.now()).total_seconds() / 3600
            if hours_before_event > 48:
                refund_percentage = 100
            elif hours_before_event > 24:
                refund_percentage = 50
            else:
                refund_percentage = 0
                
            refund_requests_data.append({
                'id': refund.id,
                'user_name': refund.registration.user.username,
                'event_id': refund.registration.session.model.event.id,
                'event_title': refund.registration.session.model.event.title,
                'model_name': refund.registration.session.model.name,
                'session_id': refund.registration.session.id,
                'session_title': refund.registration.session.title,
                'session_time': f"{refund.registration.session.start_time.strftime('%H:%M')}-{refund.registration.session.end_time.strftime('%H:%M')}",
                'created_at': refund.created_at.strftime('%Y-%m-%d %H:%M'),
                'amount': str(refund.amount),
                'reason': refund.reason,
                'refund_percentage': refund_percentage
            })
        
        return JsonResponse({
            'success': True,
            'refund_requests': refund_requests_data
        })
    
    return render(request, 'event/pending_refunds.html', {'pending_refunds': pending_refunds})


@login_required
def request_refund(request, registration_id):
    """申请退款"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '无效的请求方法'})
    
    try:
        # 获取报名记录
        registration = get_object_or_404(
            EventRegistration, 
            id=registration_id, 
            user=request.user
        )
        
        # 检查是否已经提交过退款申请
        existing_refund = RefundRequest.objects.filter(
            registration=registration,
            status__in=['pending', 'approved']
        ).first()
        
        if existing_refund:
            return JsonResponse({
                'success': False, 
                'message': '您已经提交过该活动的退款申请，请勿重复提交'
            })
        
        # 检查活动是否可以退款
        event = registration.session.model.event
        now = timezone.now()
        time_diff = event.event_time - now
        
        # 计算退款金额
        fee = registration.session.model.fee
        if time_diff > timedelta(hours=48):
            # 全额退款
            refund_amount = fee
        elif time_diff > timedelta(hours=24):
            # 50%退款
            refund_amount = fee * Decimal('0.5')
        else:
            # 无法退款
            return JsonResponse({
                'success': False, 
                'message': '活动开始前24小时内无法申请退款'
            })
        
        # 获取退款原因
        reason = request.POST.get('reason', '').strip()
        if not reason:
            return JsonResponse({
                'success': False, 
                'message': '请填写退款原因'
            })
        
        # 创建退款申请
        refund_request = RefundRequest.objects.create(
            registration=registration,
            amount=refund_amount,
            reason=reason,
            status='pending'
        )
        
        return JsonResponse({
            'success': True, 
            'message': '退款申请已提交，请等待审核'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'申请退款时发生错误: {str(e)}'
        })


@login_required
def process_refund(request, refund_id):
    """处理退款申请"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '无效的请求方法'})
    
    try:
        # 获取退款申请
        refund_request = get_object_or_404(
            RefundRequest,
            id=refund_id,
            registration__session__model__event__created_by=request.user,
            status='pending'
        )
        
        # 获取处理动作（同意或拒绝）
        action = request.POST.get('action')
        if action not in ['approve', 'reject']:
            return JsonResponse({'success': False, 'message': '无效的操作'})
        
        if action == 'approve':
            # 同意退款
            refund_request.status = 'approved'
            refund_request.processed_at = timezone.now()
            message = '退款申请已同意'
            
            # 更新场次名额 - 增加一个名额
            session = refund_request.registration.session
            # 注意：这里我们不直接增加名额，而是将该注册标记为已退款，这样就不会占用名额了
            # 如果需要真正增加名额，应该修改EventSession模型以支持动态名额管理
            
            # 更新报名状态 - 将注册标记为已退款
            registration = refund_request.registration
            registration.is_refunded = True
            registration.save()
        else:
            # 拒绝退款
            refund_request.status = 'rejected'
            refund_request.processed_at = timezone.now()
            message = '退款申请已拒绝'
        
        # 保存更改
        refund_request.save()
        
        return JsonResponse({
            'success': True, 
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'处理退款申请时发生错误: {str(e)}'
        })
