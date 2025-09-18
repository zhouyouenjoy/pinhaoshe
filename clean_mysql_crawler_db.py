#!/usr/bin/env python
"""
清理MySQL中crawler_db数据库里不属于crawler应用的表
"""

import mysql.connector
from mysql.connector import Error

def clean_crawler_database():
    try:
        # 连接到MySQL数据库
        connection = mysql.connector.connect(
            host='localhost',
            database='crawler_db',
            user='root',
            password='123456',
            port=3306
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 禁用外键检查以避免删除顺序问题
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 获取crawler_db数据库中的所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            # crawler应用应有的表（以crawler_开头）
            crawler_prefix = 'crawler_'
            
            # 需要删除的表
            tables_to_drop = []
            for table in tables:
                table_name = table[0]
                # 如果表不是crawler应用的表，则需要删除
                if not table_name.startswith(crawler_prefix):
                    tables_to_drop.append(table_name)
            
            # 删除不属于crawler应用的表
            for table_name in tables_to_drop:
                print(f"删除表: {table_name}")
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
            
            # 重新启用外键检查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            connection.commit()
            print(f"清理完成，删除了 {len(tables_to_drop)} 个不属于crawler应用的表")
            
            # 显示剩余的表
            cursor.execute("SHOW TABLES")
            remaining_tables = cursor.fetchall()
            print("crawler_db数据库中剩余的表:")
            for table in remaining_tables:
                print(f"  - {table[0]}")
                
    except Error as e:
        print(f"数据库错误: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL连接已关闭")

if __name__ == "__main__":
    clean_crawler_database()