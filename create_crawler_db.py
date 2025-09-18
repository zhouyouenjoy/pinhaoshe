import pymysql
import sys

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8mb4'
}

def create_database():
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            charset=DB_CONFIG['charset']
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS crawler_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("数据库 'crawler_db' 创建成功或已存在")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"创建数据库时出错: {e}")
        return False

if __name__ == "__main__":
    if create_database():
        print("数据库创建完成")
    else:
        print("数据库创建失败")
        sys.exit(1)