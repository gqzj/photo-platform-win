# -*- coding: utf-8 -*-
"""
为styles表添加manual字段，用于标识是否为手工风格
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'photo_platform')
    }

def add_manual_field():
    """添加manual字段到styles表"""
    db_config = get_db_config()
    
    connection = None
    try:
        connection = pymysql.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 3306),
            user=db_config.get('user', 'root'),
            password=db_config.get('password', ''),
            database=db_config.get('database', 'photo_platform'),
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'styles' 
            AND COLUMN_NAME = 'manual'
        """, (db_config.get('database'),))
        
        if cursor.fetchone()[0] > 0:
            print("字段 manual 已存在，跳过添加")
        else:
            # 添加manual字段
            cursor.execute("""
                ALTER TABLE `styles` 
                ADD COLUMN `manual` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为手工风格：0-否，1-是' 
                AFTER `sample_set_id`
            """)
            connection.commit()
            print("[OK] 成功添加 manual 字段到 styles 表")
        
    except Exception as e:
        print(f"[ERROR] 添加字段失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    add_manual_field()
