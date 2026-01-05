# -*- coding: utf-8 -*-
"""
修复aesthetic_scores表中image_id为NULL的记录
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def fix_null_image_id():
    """修复image_id为NULL的记录"""
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
            # 查找image_id为NULL的记录
            cursor.execute("""
                SELECT id, style_id, evaluator_type, created_at 
                FROM aesthetic_scores 
                WHERE image_id IS NULL
            """)
            null_records = cursor.fetchall()
            
            if null_records:
                print(f"找到 {len(null_records)} 条image_id为NULL的记录")
                for record in null_records:
                    record_id, style_id, evaluator_type, created_at = record
                    print(f"  记录ID: {record_id}, 风格ID: {style_id}, 评分器类型: {evaluator_type}, 创建时间: {created_at}")
                
                # 删除这些无效记录
                cursor.execute("""
                    DELETE FROM aesthetic_scores 
                    WHERE image_id IS NULL
                """)
                connection.commit()
                print(f"已删除 {len(null_records)} 条无效记录")
            else:
                print("没有找到image_id为NULL的记录")
            
    except Exception as e:
        print(f"修复失败: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    fix_null_image_id()

