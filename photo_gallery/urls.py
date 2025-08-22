"""
URL configuration for photo_gallery project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# 从django.contrib模块导入admin，用于管理后台
from django.contrib import admin
# 从django.urls模块导入path和include函数，用于定义URL模式
from django.urls import path, include
# 从django.contrib.auth导入LogoutView
from django.contrib.auth.views import LogoutView
# 从django.conf模块导入settings，用于访问项目设置
from django.conf import settings
# 从django.conf.urls.static导入static，用于处理静态文件
from django.conf.urls.static import static

# urlpatterns是URL模式的列表，定义了URL与视图函数的映射关系
urlpatterns = [
    # 管理后台URL，访问/admin/时会进入Django管理界面
    path('admin/', admin.site.urls),
    
    # 包含photos应用的URL模式，将空字符串的路径交给photos应用处理
    # 这意味着访问网站根路径时会由photos应用处理
    path('', include('photos.urls')),
    
    # 单独配置登出视图，允许GET请求并设置重定向页面
    # 注意：必须放在包含django.contrib.auth.urls之前，以确保优先匹配
    path('accounts/logout/', LogoutView.as_view(next_page='/', http_method_names=['get', 'post']), name='logout'),
    
    # 包含Django内置的认证URL模式，如登录、登出等
    # 这些URL会以/accounts/为前缀，例如/accounts/login/
    path('accounts/', include('django.contrib.auth.urls')),
]

# 如果是调试模式（开发环境），则添加媒体文件的URL模式
# 这样可以通过URL直接访问用户上传的媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)