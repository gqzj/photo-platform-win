# -*- coding: utf-8 -*-
"""
为lut_files表的category_id和original_filename字段添加联合唯一索引
"""
import sys
import os
import pymysql
from dotenv import load_dotenv

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()

def add_unique_index():
    """添加联合唯一索引"""
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
            # 检查是否已存在该索引
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.statistics 
                WHERE table_schema = DATABASE() 
                AND table_name = 'lut_files' 
                AND index_name = 'uk_category_original_filename'
            """)
            index_exists = cursor.fetchone()[0] > 0
            
            if index_exists:
                print("✓ 联合唯一索引已存在，跳过")
                return
            
            # 检查是否有重复数据
            cursor.execute("""
                SELECT category_id, original_filename, COUNT(*) as cnt
                FROM lut_files
                GROUP BY category_id, original_filename
                HAVING cnt > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                print("✗ 发现重复数据，无法创建唯一索引：")
                for dup in duplicates:
                    category_id = dup[0] if dup[0] is not None else 'NULL'
                    print(f"  - category_id: {category_id}, original_filename: {dup[1]}, 数量: {dup[2]}")
                print("\n请先处理重复数据后再执行此脚本")
                return
            
            # 添加联合唯一索引
            sql = """
            ALTER TABLE `lut_files` 
            ADD UNIQUE KEY `uk_category_original_filename` (`category_id`, `original_filename`)
            """
            
            cursor.execute(sql)
            connection.commit()
            print("✓ 联合唯一索引 `uk_category_original_filename` 创建成功")
            
    except Exception as e:
        print(f"✗ 创建索引失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("开始为lut_files表添加联合唯一索引...")
    add_unique_index()
    print("完成！")

