from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Photo, Album

# Register your models here.
class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ('image_preview', 'id', 'uploaded_at', 'approved')
    readonly_fields = ('image_preview', 'id', 'uploaded_at')
    can_delete = True
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "无图片"
    image_preview.short_description = "图片预览"


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    # 添加图片预览方法
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "无图片"
    image_preview.short_description = "图片预览"
    
    # 列表显示的字段
    list_display = ('id', 'uploaded_by', 'uploaded_at', 'approved', 'image_preview')
    
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
    inlines = [PhotoInline]
    
    # 列表显示的字段
    list_display = ('title', 'uploaded_by', 'uploaded_at', 'approved', 'photo_count')
    
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
    
    # 添加一个方法来显示照片数量
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _photo_count=Count("photo", distinct=True),
        )
    
    def photo_count(self, obj):
        return obj._photo_count
    photo_count.short_description = '照片数量'
    photo_count.admin_order_field = '_photo_count'