# -*- coding: utf-8 -*-
"""
修复 sample_set_images 表结构，添加缺失的 matched_features 字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def fix_table():
    """修复 sample_set_images 表结构"""
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
            # 检查并添加 matched_features 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_set_images' 
                AND COLUMN_NAME = 'matched_features'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 matched_features 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_set_images` 
                    ADD COLUMN `matched_features` TEXT 
                    COMMENT '匹配的特征JSON，记录哪些特征匹配' 
                    AFTER `image_id`
                """)
                connection.commit()
                print("[成功] matched_features 字段添加成功")
            else:
                print("[信息] matched_features 字段已存在，无需修改")
            
            print("[完成] 表结构修复完成")
                
    except Exception as e:
        print(f"修复表结构失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    fix_table()

