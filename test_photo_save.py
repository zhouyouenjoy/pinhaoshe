import os
import sys

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')

import django
django.setup()

def test_photo_save():
    """测试Photo数据保存功能"""
    try:
        from crawler.models import CrawlerUser, Album, Photo
        
        # 获取或创建测试用户
        user, created = CrawlerUser.objects.using('crawler').get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'is_staff': False,
                'is_active': True,
                'is_superuser': False,
                'password': 'pbkdf2_sha256$260000$AIgaFC17pg0j3dM65xrI0w$gcbS6m0S0I2F8wQ8S14GFgEz2nIQTM0gD5nVjE5V9uM=',  # 123456@
            }
        )
        print(f"用户: {'已创建' if created else '已存在'}")

        # 创建测试相册
        album, created = Album.objects.using('crawler').get_or_create(
            title='测试相册',
            defaults={
                'description': '测试相册描述',
                'uploaded_by': user,
            }
        )
        print(f"相册: {'已创建' if created else '已存在'}")

        # 创建测试照片
        photo, created = Photo.objects.using('crawler').get_or_create(
            title='测试照片',
            external_url='https://example.com/test.jpg',
            defaults={
                'description': '测试照片描述',
                'uploaded_by': user,
                'album': album,
            }
        )
        print(f"照片: {'已创建' if created else '已存在'}")
        print(f"照片标题: {photo.title}")
        print(f"照片URL: {photo.external_url}")
        print(f"关联相册: {photo.album.title if photo.album else '无'}")
        
        # 验证数据保存
        photos = Photo.objects.using('crawler').filter(album=album)
        print(f"相册中的照片数量: {photos.count()}")
        
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_photo_save()