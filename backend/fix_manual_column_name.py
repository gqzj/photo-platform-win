# -*- coding: utf-8 -*-
"""
将styles表的manual字段重命名为is_manual，避免MySQL保留关键字冲突
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

def fix_manual_column():
    """将manual字段重命名为is_manual"""
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
        
        # 检查字段是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'styles' 
            AND COLUMN_NAME = 'manual'
        """, (db_config.get('database'),))
        
        if cursor.fetchone()[0] > 0:
            # 检查is_manual字段是否已存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'styles' 
                AND COLUMN_NAME = 'is_manual'
            """, (db_config.get('database'),))
            
            if cursor.fetchone()[0] == 0:
                # 重命名字段
                cursor.execute("""
                    ALTER TABLE `styles` 
                    CHANGE COLUMN `manual` `is_manual` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为手工风格：0-否，1-是'
                """)
                connection.commit()
                print("[OK] 成功将 manual 字段重命名为 is_manual")
            else:
                print("字段 is_manual 已存在，跳过重命名")
        else:
            print("字段 manual 不存在，可能已经重命名或使用其他名称")
        
    except Exception as e:
        print(f"[ERROR] 重命名字段失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    fix_manual_column()
