"""
创建需求管理表
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

def create_table():
    """创建需求管理表"""
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
        
        # 检查表是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'requirements'
        """, (db_config.get('database', 'photo_platform'),))
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("表 requirements 已存在，跳过创建")
        else:
            # 创建需求管理表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requirements (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                    name VARCHAR(200) NOT NULL COMMENT '需求名称',
                    requester VARCHAR(100) COMMENT '需求发起人',
                    keywords_json TEXT COMMENT '抓取的关键字范围JSON',
                    cleaning_features_json TEXT COMMENT '清洗任务的筛选特征JSON',
                    tagging_features_json TEXT COMMENT '需要打标的特征JSON',
                    sample_set_features_json TEXT COMMENT '样本集的特征范围JSON',
                    status VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '状态：pending(待处理), active(进行中), completed(已完成), cancelled(已取消)',
                    note TEXT COMMENT '备注',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_status (status),
                    INDEX idx_requester (requester)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='需求管理表'
            """)
            connection.commit()
            print("成功创建 requirements 表")
        
    except Exception as e:
        print(f"创建表失败: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    create_table()

