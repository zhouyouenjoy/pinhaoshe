import requests
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')
django.setup()

from photos.models import Photo
from django.contrib.auth.models import User

# 获取所有image字段存在但external_url为空的照片
try:
    # 查找所有image字段存在但external_url为空的照片
    photos = Photo.objects.exclude(image__isnull=True).exclude(image='').filter(external_url__isnull=True).order_by('uploaded_at')
    print(f"Found {photos.count()} photos with local images but no external URL")
    
    # 为每个照片上传到外部图床
    for photo in photos:
        print(f"Processing photo ID: {photo.id}")
        print(f"Photo path: {photo.image.path}")
        
        # 检查照片文件是否存在
        if photo.image and os.path.exists(photo.image.path):
            # 上传到外部图床
            url = "https://api.superbed.cn/upload"
            token = "23ca519693e9407e8a7dc7e98c7be36a"
            
            # 通过文件上传
            with open(photo.image.path, "rb") as f:
                files = {"file": (os.path.basename(photo.image.path), f)}
                data = {"token": token}
                resp = requests.post(url, data=data, files=files)
                
            
            # 如果上传成功，保存外部链接到数据库
            response_data = resp.json()
            # 修复判断条件，根据实际返回的数据结构来判断
            if response_data.get("err") == 0:  
                # 修复获取URL的方式，根据实际返回的数据结构来获取
                external_url = response_data.get("url") or response_data.get("data", {}).get("url")
                photo.external_url = external_url
                photo.save()
                print(f"External URL saved to database: {photo.external_url}")
            else:
                print(f"Upload failed: {response_data}")
        else:
            print("Photo file does not exist")
        print("-" * 50)
        
except Exception as e:
    print(f"Error: {e}")