"""
修复crawler_tasks表的target_url字段，允许为NULL
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

def fix_target_url_nullable():
    """修复target_url字段，允许为NULL"""
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
        
        # 检查字段当前的定义
        cursor.execute("""
            SELECT IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'crawler_tasks' 
            AND COLUMN_NAME = 'target_url'
        """, (db_config.get('database', 'photo_platform'),))
        
        result = cursor.fetchone()
        if result:
            is_nullable = result[0]
            if is_nullable == 'NO':
                # 字段不允许为NULL，需要修改
                cursor.execute("""
                    ALTER TABLE `crawler_tasks` 
                    MODIFY COLUMN `target_url` VARCHAR(2000) NULL COMMENT '目标URL'
                """)
                connection.commit()
                print("成功修改 target_url 字段，允许为 NULL")
            else:
                print("target_url 字段已经允许为 NULL，无需修改")
        else:
            print("未找到 target_url 字段")
        
    except Exception as e:
        print(f"修改字段失败: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    fix_target_url_nullable()

