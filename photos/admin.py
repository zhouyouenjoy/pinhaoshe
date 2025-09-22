from django.contrib import admin
from .models import Photo, Album

# Register your models here.
@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    # 列表显示的字段
    list_display = ('id', 'uploaded_by', 'uploaded_at', 'approved')
    
    # 可以直接在列表页编辑的字段
    list_editable = ('approved',)
    
    # 列表过滤器
    list_filter = ('approved', 'uploaded_at', 'uploaded_by')
    
    # 搜索字段
    search_fields = ('id', 'uploaded_by__username')
    
    # 按时间降序排列
    ordering = ('-uploaded_at',)
    
    # 每页显示的数量
    list_per_page = 20
    
    # 日期层级筛选
    date_hierarchy = 'uploaded_at'


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    # 列表显示的字段
    list_display = ('title', 'uploaded_by', 'uploaded_at', 'approved')
    
    # 可以直接在列表页编辑的字段
    list_editable = ('approved',)
    
    # 列表过滤器
    list_filter = ('approved', 'uploaded_at', 'uploaded_by')
    
    # 搜索字段
    search_fields = ('title', 'description', 'uploaded_by__username')
    
    # 按时间降序排列
    ordering = ('-uploaded_at',)
    
    # 每页显示的数量
    list_per_page = 20
    
    # 日期层级筛选
    date_hierarchy = 'uploaded_at'