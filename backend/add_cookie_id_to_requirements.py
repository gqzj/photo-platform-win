# -*- coding: utf-8 -*-
"""
为requirements表添加cookie_id字段
"""
import pymysql
import os
import json
from pathlib import Path

def add_cookie_id_to_requirements():
    """为requirements表添加cookie_id字段"""
    try:
        # 尝试从.env文件读取配置
        env_path = Path(__file__).parent / '.env'
        db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'photo_platform',
            'charset': 'utf8mb4'
        }
        
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            db_config['host'] = os.getenv('MYSQL_HOST') or os.getenv('DB_HOST', db_config['host'])
            db_config['port'] = int(os.getenv('MYSQL_PORT') or os.getenv('DB_PORT', db_config['port']))
            db_config['user'] = os.getenv('MYSQL_USER') or os.getenv('DB_USER', db_config['user'])
            db_config['password'] = os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD', db_config['password'])
            db_config['database'] = os.getenv('MYSQL_DATABASE') or os.getenv('DB_NAME', db_config['database'])
        
        # 如果.env不存在，尝试从config.json读取
        if not env_path.exists():
            config_path = Path(__file__).parent / 'config.json'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    db_config = config.get('database', db_config)
        
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'requirements' 
            AND COLUMN_NAME = 'cookie_id'
        """, (db_config['database'],))
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("字段 cookie_id 已存在，跳过添加")
        else:
            # 添加cookie_id字段
            cursor.execute("""
                ALTER TABLE requirements 
                ADD COLUMN cookie_id INT NULL COMMENT '抓取任务使用的账号ID（Cookie ID）' 
                AFTER keywords_json
            """)
            connection.commit()
            print("成功添加 cookie_id 字段到 requirements 表")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"添加字段失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_cookie_id_to_requirements()

