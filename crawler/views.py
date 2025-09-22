from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import CrawlerUser, CrawledPost


def post_list(request):
    """
    展示爬取的内容列表
    """
    posts = CrawledPost.objects.using('crawler').select_related('user').prefetch_related('media_files').order_by('-posted_at')
    
    # 分页处理
    paginator = Paginator(posts, 12)  # 每页显示12个内容
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'crawler/post_list.html', {
        'posts': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })


def post_detail(request, post_id):
    """
    展示爬取内容的详情
    """
    post = get_object_or_404(CrawledPost.objects.using('crawler').select_related('user').prefetch_related('media_files'), id=post_id)
    
    return render(request, 'crawler/post_detail.html', {
        'post': post,
    })


def user_list(request):
    """
    展示爬取的用户列表
    """
    users = CrawlerUser.objects.using('crawler').all().order_by('id')

    # 分页处理
    paginator = Paginator(users, 20)  # 每页显示20个用户
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'crawler/user_list.html', {
        'users': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })


def crawl_page(request):
    """
    显示爬取页面
    """
    return render(request, 'crawler/crawl_page.html')