from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models  import CrawledUser, CrawledPost, CrawledMedia
from . import spiders

def post_list(request):
    """
    展示爬取的内容列表
    """
    posts = CrawledPost.objects.select_related('user').prefetch_related('media_files').order_by('-posted_at')
    
    # 分页处理
    paginator = Paginator(posts, 12)  # 每页显示12个内容
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'crawler/post_list.html', {
        'posts': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })


def user_list(request):
    """
    展示爬取的用户列表
    """
    users = CrawledUser.objects.order_by('-created_at')
    
    # 分页处理
    paginator = Paginator(users, 20)  # 每页显示20个用户
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'crawler/user_list.html', {
        'users': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })


def post_detail(request, post_id):
    """
    展示内容详情
    """
    post = get_object_or_404(CrawledPost.objects.select_related('user').prefetch_related('media_files'), id=post_id)
    return render(request, 'crawler/post_detail.html', {'post': post})


def crawl_page(request):
    """
    爬取页面，让用户选择平台和用户进行爬取
    """
    if request.method == 'POST':
        # 处理爬取请求
        platform = request.POST.get('platform')
        username = request.POST.get('username')
        album_url = request.POST.get('album_url')
        download_media = request.POST.get('download_media')
        
        # 根据平台选择相应的爬虫类
        if platform == 'douyin':
            spider = spiders.DouyinSpider(headless=False)
        elif platform == 'xiaohongshu':
            spider = spiders.XiaohongshuSpider(headless=False)
        elif platform == 'bilibili':
            spider = spiders.BilibiliSpider(headless=False)
        else:
            return JsonResponse({
                'status': 'error',
                'message': '不支持的平台'
            })
        
        print(f"platform: {platform}")
        # 连接到已运行的浏览器，而不是启动新浏览器
        spider.init_driver()
        print(f"打印当前页面标题：{spider.driver.title}")
        
        # 这里应该实现实际的爬虫逻辑
        # 目前只是模拟返回成功响应
        return JsonResponse({
            'status': 'success',
            'message': f'已开始爬取 {platform} 平台用户 {username} 的数据'
        })
    
    # GET请求显示爬取页面
    return render(request, 'crawler/crawl_page.html')