"""
创建特征组相关表
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

def create_tables():
    """创建特征组相关表"""
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
        
        # 1. 创建特征组表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `feature_groups` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `name` VARCHAR(200) NOT NULL COMMENT '特征组名称',
                `description` TEXT COMMENT '特征组描述',
                `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY `uk_name` (`name`),
                INDEX `idx_enabled` (`enabled`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='特征组表';
        """)
        print("特征组表创建成功")
        
        # 2. 创建特征组-特征关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `feature_group_features` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `feature_group_id` INT NOT NULL COMMENT '特征组ID',
                `feature_id` INT NOT NULL COMMENT '特征ID',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                UNIQUE KEY `uk_group_feature` (`feature_group_id`, `feature_id`),
                INDEX `idx_group` (`feature_group_id`),
                INDEX `idx_feature` (`feature_id`),
                FOREIGN KEY (`feature_group_id`) REFERENCES `feature_groups` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`feature_id`) REFERENCES `features` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='特征组-特征关联表';
        """)
        print("特征组-特征关联表创建成功")
        
        connection.commit()
        print("所有表创建完成")
        
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
    create_tables()

