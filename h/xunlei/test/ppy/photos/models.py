from django.db import models
from django.contrib.auth.models import User

# 定义Photo模型，继承自Django的Model类
class Photo(models.Model):
    # 标题字段，CharField是字符串字段，最大长度为200个字符
    title = models.CharField(max_length=200)
    
    # 图片字段，ImageField用于存储图片文件
    # upload_to参数指定图片上传到media/photos/目录下
    image = models.ImageField(upload_to='photos/')
    
    # 描述字段，TextField是长文本字段，blank=True表示可以为空
    description = models.TextField(blank=True)
    
    # 上传者字段，ForeignKey表示外键关联到User模型
    # on_delete=models.CASCADE表示当关联的用户被删除时，该照片也会被删除
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # 上传时间字段，DateTimeField类型
    # auto_now_add=True表示对象第一次创建时自动设置为当前时间，之后不会改变
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # 审核状态字段，BooleanField是布尔字段，默认值为False（未审核）
    approved = models.BooleanField(default=False)
    
    # 添加展示图标记字段
    is_display_image = models.BooleanField(default=False, help_text="是否作为相册展示图")
    
    # 添加与Album的关联（可选），使用字符串引用避免循环导入
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null=True, blank=True)
    
    # 定义模型的字符串表示方法，返回照片的标题
    def __str__(self):
        return self.title
