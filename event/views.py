from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event
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
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            # 默认需要审核
            event.approved = False
            event.save()
            messages.success(request, '活动创建成功，等待管理员审核！')
            return redirect('event:event_list')
    else:
        form = EventForm()
    
    return render(request, 'event/create_event.html', {
        'form': form
    })