# -*- coding: utf-8 -*-
"""
检查 sample_sets 表的所有字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def check_columns():
    """检查表的所有字段"""
    # 数据库连接配置
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'photo_platform'),
        'charset': 'utf8mb4'
    }
    
    connection = pymysql.connect(**config)
    
    try:
        with connection.cursor() as cursor:
            # 获取所有字段
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_sets'
                ORDER BY ORDINAL_POSITION
            """, (config['database'],))
            
            columns = cursor.fetchall()
            
            print("sample_sets 表的所有字段:")
            print("-" * 80)
            for col in columns:
                col_name, col_type, is_nullable, col_default, col_comment = col
                print(f"字段名: {col_name}")
                print(f"  类型: {col_type}")
                print(f"  可空: {is_nullable}")
                print(f"  默认值: {col_default}")
                print(f"  注释: {col_comment}")
                print("-" * 80)
                
    except Exception as e:
        print(f"检查字段失败: {e}")
    finally:
        connection.close()

if __name__ == '__main__':
    check_columns()

