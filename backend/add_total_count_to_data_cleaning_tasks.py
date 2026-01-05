"""
为数据清洗任务表添加total_count字段（需要清洗的图片总数）
"""
import pymysql
import os
from dotenv import load_dotenv

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

def add_column():
    """添加total_count字段"""
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
            AND TABLE_NAME = 'data_cleaning_tasks' 
            AND COLUMN_NAME = 'total_count'
        """, (db_config.get('database', 'photo_platform'),))
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("字段 total_count 已存在，跳过添加")
        else:
            # 添加total_count字段
            cursor.execute("""
                ALTER TABLE `data_cleaning_tasks` 
                ADD COLUMN `total_count` INT NOT NULL DEFAULT 0 COMMENT '需要清洗的图片总数' 
                AFTER `processed_count`
            """)
            connection.commit()
            print("成功添加 total_count 字段")
        
    except Exception as e:
        print(f"添加字段失败: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    add_column()

