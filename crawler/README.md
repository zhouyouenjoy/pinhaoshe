# 爬虫应用使用说明

## 简介

本应用用于从抖音、小红书、B站等平台爬取照片数据。为了不干扰主数据库，爬虫数据存储在独立的MySQL数据库中。

## 数据模型

### CrawledUser (爬取用户)
存储从平台上爬取的用户信息：
- username: 用户名
- nickname: 昵称
- avatar_url: 头像链接
- platform: 平台(douyin, xiaohongshu, bilibili)
- follower_count: 粉丝数
- following_count: 关注数
- post_count: 发布内容数

### CrawledPost (爬取内容)
存储从平台上爬取的内容信息：
- title: 内容标题
- content: 内容文本
- image_urls: 图片URL列表
- user: 关联的用户
- platform: 平台
- posted_at: 发布时间
- like_count: 点赞数
- comment_count: 评论数
- share_count: 分享数

### CrawledMedia (爬取媒体)
存储从平台上爬取的媒体文件信息：
- media_type: 媒体类型(image, video)
- url: 媒体链接
- local_path: 本地存储路径
- post: 关联的内容
- platform: 平台
- downloaded_at: 下载时间
- is_downloaded: 是否已下载

## 数据库配置

爬虫应用使用独立的MySQL数据库：
- 数据库名称：`crawler_db`
- 数据库别名：`crawler`

## 前端页面

应用提供以下前端页面用于展示爬取的数据：
- 爬取页面：`/crawler/` 或 `/crawler/crawl/`
- 用户列表页面：`/crawler/users/`
- 用户详情页面：`/crawler/users/<user_id>/`
- 相册详情页面：`/crawler/albums/<album_id>/`

## 使用方法

### 1. 创建数据库
在MySQL中创建[crawler_db](file:///h:\xunlei\test\ppy\crawler_db)数据库：
```sql
CREATE DATABASE IF NOT EXISTS crawler_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 运行数据库迁移
```bash
python manage.py migrate --database=crawler
```

### 3. 测试应用
```bash
python manage.py test_crawler
```

### 4. 开发爬虫功能
在 `spiders.py` 中实现具体的爬虫逻辑：
- `DouyinSpider`: 抖音爬虫
- `XiaohongshuSpider`: 小红书爬虫
- `BilibiliSpider`: B站爬虫

### 5. 使用Selenium爬取数据
爬虫使用Selenium框架进行数据爬取，需要安装ChromeDriver。

安装依赖：
```bash
pip install selenium
```

## 爬取页面功能

爬取页面允许用户：
1. 选择目标平台（抖音、小红书、B站）
2. 输入用户ID或用户名
3. 指定特定相册链接（可选，留空则爬取用户所有相册）
4. 选择是否同时下载媒体文件

页面会显示爬取进度和状态信息。

用户头像、相册标题和描述会自动从平台获取，用户无需手动输入。

## 注意事项

1. 爬虫操作可能违反平台服务条款，请在合法合规的前提下使用
2. 注意控制爬取频率，避免对平台造成过大压力
3. 爬取的数据仅供内部学习研究使用，不得用于商业用途
4. 部分平台可能有反爬虫机制，需要适当处理