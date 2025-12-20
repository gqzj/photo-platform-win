# -*- coding: utf-8 -*-
"""
修复 sample_set_features 表结构，添加缺失的字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def fix_table():
    """修复 sample_set_features 表结构"""
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
            # 检查并添加 feature_name 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_set_features' 
                AND COLUMN_NAME = 'feature_name'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 feature_name 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_set_features` 
                    ADD COLUMN `feature_name` VARCHAR(100) NOT NULL DEFAULT '' 
                    COMMENT '特征名称' 
                    AFTER `feature_id`
                """)
                print("[成功] feature_name 字段添加成功")
            else:
                print("[信息] feature_name 字段已存在")
            
            # 检查并添加 value_range 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_set_features' 
                AND COLUMN_NAME = 'value_range'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 value_range 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_set_features` 
                    ADD COLUMN `value_range` TEXT 
                    COMMENT '特征取值范围JSON' 
                    AFTER `feature_name`
                """)
                print("[成功] value_range 字段添加成功")
            else:
                print("[信息] value_range 字段已存在")
            
            # 检查并添加 value_type 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_set_features' 
                AND COLUMN_NAME = 'value_type'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 value_type 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_set_features` 
                    ADD COLUMN `value_type` VARCHAR(50) NOT NULL DEFAULT 'enum' 
                    COMMENT '值类型：enum, range, any' 
                    AFTER `value_range`
                """)
                print("[成功] value_type 字段添加成功")
            else:
                print("[信息] value_type 字段已存在")
            
            # 检查并添加 updated_at 字段
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_set_features' 
                AND COLUMN_NAME = 'updated_at'
            """, (config['database'],))
            
            if cursor.fetchone()[0] == 0:
                print("检测到缺少 updated_at 字段，正在添加...")
                cursor.execute("""
                    ALTER TABLE `sample_set_features` 
                    ADD COLUMN `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
                    COMMENT '更新时间' 
                    AFTER `created_at`
                """)
                print("[成功] updated_at 字段添加成功")
            else:
                print("[信息] updated_at 字段已存在")
            
            connection.commit()
            print("[完成] 表结构修复完成")
                
    except Exception as e:
        print(f"修复表结构失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    fix_table()

