# -*- coding: utf-8 -*-
"""
修复 sample_sets 表结构，添加缺失的 status 字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def fix_table():
    """修复 sample_sets 表结构"""
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
            # 检查 status 字段是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_sets' 
                AND COLUMN_NAME = 'status'
            """, (config['database'],))
            
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                print("检测到 sample_sets 表缺少 status 字段，正在添加...")
                # 添加 status 字段
                cursor.execute("""
                    ALTER TABLE `sample_sets` 
                    ADD COLUMN `status` VARCHAR(50) NOT NULL DEFAULT 'active' 
                    COMMENT '状态：active, inactive' 
                    AFTER `description`
                """)
                # 添加索引
                cursor.execute("""
                    ALTER TABLE `sample_sets` 
                    ADD INDEX `idx_status` (`status`)
                """)
                connection.commit()
                print("[成功] status 字段添加成功")
            else:
                print("[信息] status 字段已存在，无需修改")
            
            # 检查并添加其他缺失字段
            required_fields = {
                'name': "VARCHAR(200) NOT NULL COMMENT '样本集名称'",
                'description': "TEXT COMMENT '样本集描述'",
                'image_count': "INT NOT NULL DEFAULT 0 COMMENT '图片数量'",
                'created_at': "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
                'updated_at': "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'"
            }
            
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'sample_sets'
            """, (config['database'],))
            
            existing_fields = [row[0] for row in cursor.fetchall()]
            
            # 添加缺失字段
            for field_name, field_def in required_fields.items():
                if field_name not in existing_fields:
                    print(f"检测到缺少 {field_name} 字段，正在添加...")
                    try:
                        if field_name == 'name':
                            cursor.execute(f"ALTER TABLE `sample_sets` ADD COLUMN `{field_name}` {field_def} FIRST")
                        elif field_name == 'description':
                            cursor.execute(f"ALTER TABLE `sample_sets` ADD COLUMN `{field_name}` {field_def} AFTER `name`")
                        elif field_name == 'image_count':
                            cursor.execute(f"ALTER TABLE `sample_sets` ADD COLUMN `{field_name}` {field_def} AFTER `status`")
                        elif field_name == 'created_at':
                            cursor.execute(f"ALTER TABLE `sample_sets` ADD COLUMN `{field_name}` {field_def} AFTER `image_count`")
                        elif field_name == 'updated_at':
                            cursor.execute(f"ALTER TABLE `sample_sets` ADD COLUMN `{field_name}` {field_def} AFTER `created_at`")
                        print(f"[成功] {field_name} 字段添加成功")
                    except Exception as e:
                        print(f"[错误] 添加 {field_name} 字段失败: {e}")
            
            connection.commit()
            print("[完成] 表结构修复完成")
                
    except Exception as e:
        print(f"修复表结构失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    fix_table()

