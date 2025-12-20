# -*- coding: utf-8 -*-
"""
在sample_sets表中添加打包相关字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def add_fields():
    """添加打包相关字段"""
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
            # 检查并添加 package_status 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_sets' 
                AND COLUMN_NAME = 'package_status'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 package_status 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_sets` 
                    ADD COLUMN `package_status` VARCHAR(50) NOT NULL DEFAULT 'unpacked' 
                    COMMENT '打包状态：unpacked(未打包), packing(打包中), packed(已打包), failed(打包失败)' 
                    AFTER `image_count`
                """)
                print("[成功] package_status 字段添加成功")
            else:
                print("[信息] package_status 字段已存在")
            
            # 检查并添加 package_path 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_sets' 
                AND COLUMN_NAME = 'package_path'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 package_path 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_sets` 
                    ADD COLUMN `package_path` VARCHAR(500) 
                    COMMENT '压缩包存储路径' 
                    AFTER `package_status`
                """)
                print("[成功] package_path 字段添加成功")
            else:
                print("[信息] package_path 字段已存在")
            
            # 检查并添加 packaged_at 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_sets' 
                AND COLUMN_NAME = 'packaged_at'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 packaged_at 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_sets` 
                    ADD COLUMN `packaged_at` DATETIME 
                    COMMENT '打包完成时间' 
                    AFTER `package_path`
                """)
                print("[成功] packaged_at 字段添加成功")
            else:
                print("[信息] packaged_at 字段已存在")
            
            connection.commit()
            print("[完成] 表结构修复完成")
                
    except Exception as e:
        print(f"修复表结构失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    add_fields()

