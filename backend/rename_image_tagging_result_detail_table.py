"""
重命名表 image_tagging_result_detail 为 image_tagging_results_detail
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

def rename_table():
    """重命名表"""
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
        
        # 检查旧表是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'image_tagging_result_detail'
        """, (db_config.get('database', 'photo_platform'),))
        
        old_table_exists = cursor.fetchone()[0] > 0
        
        if not old_table_exists:
            print("表 image_tagging_result_detail 不存在，无需重命名")
            return
        
        # 检查新表是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'image_tagging_results_detail'
        """, (db_config.get('database', 'photo_platform'),))
        
        new_table_exists = cursor.fetchone()[0] > 0
        
        if new_table_exists:
            print("表 image_tagging_results_detail 已存在，跳过重命名")
            return
        
        # 重命名表
        cursor.execute("""
            RENAME TABLE `image_tagging_result_detail` TO `image_tagging_results_detail`
        """)
        
        connection.commit()
        print("表重命名成功：image_tagging_result_detail -> image_tagging_results_detail")
        
    except Exception as e:
        print(f"重命名表失败: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    rename_table()

