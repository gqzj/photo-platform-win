"""
为需求表添加进度相关字段
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

def add_fields():
    """添加进度字段"""
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
            AND TABLE_NAME = 'requirements' 
            AND COLUMN_NAME = 'progress_json'
        """, (db_config.get('database', 'photo_platform'),))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `requirements` 
                ADD COLUMN `progress_json` TEXT COMMENT '进度JSON，记录各任务节点的状态和进度'
            """)
            print("添加 progress_json 字段成功")
        else:
            print("progress_json 字段已存在，跳过")
        
        connection.commit()
        
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
    add_fields()

