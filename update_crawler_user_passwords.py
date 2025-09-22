import pymysql
import os
import sys

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photo_gallery.settings')

import django
django.setup()

def update_crawler_user_passwords():
    """更新crawler数据库中所有用户记录的密码字段"""
    try:
        # 连接到crawler数据库
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='crawler_db'
        )
        
        cursor = conn.cursor()
        
        # 更新所有密码字段为空的用户记录
        update_query = """
        UPDATE crawler_crawleruser 
        SET password = %s 
        WHERE password IS NULL OR password = ''
        """
        
        # 默认密码"123456@"的哈希值
        default_password_hash = 'pbkdf2_sha256$260000$AIgaFC17pg0j3dM65xrI0w$gcbS6m0S0I2F8wQ8S14GFgEz2nIQTM0gD5nVjE5V9uM='
        
        cursor.execute(update_query, (default_password_hash,))
        affected_rows = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"成功更新了 {affected_rows} 条用户记录的密码字段")
        return affected_rows
        
    except Exception as e:
        print(f"更新用户密码时出错: {str(e)}")
        return 0

if __name__ == "__main__":
    update_crawler_user_passwords()