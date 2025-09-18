# Photo Gallery 项目

这是一个基于 Django 的照片管理系统，包含照片展示、活动管理和网络爬虫功能。

## 项目启动方式

### 推荐方式：使用 Daphne ASGI 服务器（支持 WebSocket）

由于项目使用了 Django Channels 实现 WebSocket 功能，推荐使用 Daphne ASGI 服务器启动项目：

```bash
# 安装 daphne
pip install daphne

# 使用 daphne 启动项目
python -m daphne -b 127.0.0.1 -p 8000 photo_gallery.asgi:application
```

### 开发环境方式：使用 Django 内置服务器

在开发环境中，也可以使用 Django 内置的 runserver 命令：

```bash
python manage.py runserver
```

但需要注意，runserver 命令在某些情况下可能无法正确处理 WebSocket 连接。

## 项目功能

### 照片管理
- 照片上传和展示
- 活动分类管理
- 照片标签和搜索

### 网络爬虫
- 支持从抖音、小红书、B站等平台爬取照片数据
- 通过 WebSocket 实现全双工通信
- 支持分阶段爬取和下载

### WebSocket 功能
- 实时状态更新
- 异步任务处理
- 全双工通信支持

## 技术栈

- Django 5.2.5
- Django Channels 4.3.1
- Daphne ASGI 服务器
- Selenium WebDriver
- Bootstrap 5.1.3 前端框架
- SQLite3 数据库

## 依赖安装

```bash
pip install django pillow channels channels_redis daphne
```

## 数据库初始化

```bash
python manage.py migrate
```

## 创建超级用户

```bash
python manage.py createsuperuser
```