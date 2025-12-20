# -*- coding: utf-8 -*-
"""
删除 sample_sets 表中的 labeled_done 字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def remove_field():
    """删除 labeled_done 字段"""
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
            # 检查 labeled_done 字段是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_sets' 
                AND COLUMN_NAME = 'labeled_done'
            """, (config['database'],))
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print("检测到 sample_sets 表存在 labeled_done 字段，正在删除...")
                # 删除 labeled_done 字段
                cursor.execute("""
                    ALTER TABLE `sample_sets` 
                    DROP COLUMN `labeled_done`
                """)
                connection.commit()
                print("[成功] labeled_done 字段删除成功")
            else:
                print("[信息] labeled_done 字段不存在，无需删除")
                
    except Exception as e:
        print(f"删除字段失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    remove_field()

