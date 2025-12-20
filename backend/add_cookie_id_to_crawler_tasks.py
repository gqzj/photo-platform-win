"""
为crawler_tasks表添加cookie_id字段
"""
import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_db_config():
    """从环境变量读取数据库配置"""
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'photo_platform')
    }

def add_cookie_id_column():
    """添加cookie_id字段到crawler_tasks表"""
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
            AND TABLE_NAME = 'crawler_tasks' 
            AND COLUMN_NAME = 'cookie_id'
        """, (db_config.get('database', 'photo_platform'),))
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("字段 cookie_id 已存在，跳过添加")
        else:
            # 添加cookie_id字段
            cursor.execute("""
                ALTER TABLE crawler_tasks 
                ADD COLUMN cookie_id INT NULL COMMENT '关联的Cookie ID' 
                AFTER target_url
            """)
            connection.commit()
            print("成功添加 cookie_id 字段到 crawler_tasks 表")
        
    except Exception as e:
        print(f"添加字段失败: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    add_cookie_id_column()

