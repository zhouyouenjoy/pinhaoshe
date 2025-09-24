import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')
django.setup()

# 导入模型
from crawler.models import Photo

# 检查Photo模型的字段
fields = [f.name for f in Photo._meta.get_fields()]
print("Photo model fields:")
for field in fields:
    print(f"  - {field}")

# 检查是否有display_image字段
if 'display_image' in fields:
    print("\nWARNING: display_image field still exists in Photo model!")
else:
    print("\nGood: display_image field has been removed from Photo model.")
    
# 检查是否有description字段
if 'description' in fields:
    print("\nWARNING: description field still exists in Photo model!")
else:
    print("\nGood: description field has been removed from Photo model.")