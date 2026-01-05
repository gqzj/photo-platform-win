# -*- coding: utf-8 -*-
"""
为styles表添加处理图片数和图片总数字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def add_fields():
    """添加字段"""
    connection = None
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'photo_platform'),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 检查字段是否存在
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'styles' AND COLUMN_NAME = 'processed_image_count'
            """, (os.getenv('MYSQL_DATABASE', 'photo_platform'),))
            exists_processed = cursor.fetchone()[0] > 0
            
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'styles' AND COLUMN_NAME = 'total_image_count'
            """, (os.getenv('MYSQL_DATABASE', 'photo_platform'),))
            exists_total = cursor.fetchone()[0] > 0
            
            # 添加processed_image_count字段
            if not exists_processed:
                cursor.execute("""
                    ALTER TABLE `styles` 
                    ADD COLUMN `processed_image_count` INT NOT NULL DEFAULT 0 COMMENT '已处理图片数（美学评分）' AFTER `image_count`
                """)
                print("已添加processed_image_count字段")
            else:
                print("processed_image_count字段已存在")
            
            # 添加total_image_count字段
            if not exists_total:
                cursor.execute("""
                    ALTER TABLE `styles` 
                    ADD COLUMN `total_image_count` INT NOT NULL DEFAULT 0 COMMENT '图片总数（美学评分）' AFTER `processed_image_count`
                """)
                print("已添加total_image_count字段")
            else:
                print("total_image_count字段已存在")
            
            connection.commit()
            print("字段添加完成")
            
    except Exception as e:
        print(f"添加字段失败: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    add_fields()

