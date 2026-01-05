"""
创建风格管理相关表
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
    """创建风格管理相关表"""
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
        
        # 1. 创建风格定义表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `styles` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `name` VARCHAR(200) NOT NULL COMMENT '风格名称',
                `description` TEXT COMMENT '风格描述',
                `sample_set_id` INT COMMENT '关联的样本集ID',
                `status` VARCHAR(50) NOT NULL DEFAULT 'active' COMMENT '状态：active, inactive',
                `image_count` INT NOT NULL DEFAULT 0 COMMENT '图片数量',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY `uk_name` (`name`),
                INDEX `idx_status` (`status`),
                INDEX `idx_sample_set` (`sample_set_id`),
                FOREIGN KEY (`sample_set_id`) REFERENCES `sample_sets` (`id`) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风格定义表';
        """)
        print("风格定义表创建成功")
        
        # 2. 创建风格图片表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `style_images` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `style_id` INT NOT NULL COMMENT '风格ID',
                `image_id` INT NOT NULL COMMENT '图片ID',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                UNIQUE KEY `uk_style_image` (`style_id`, `image_id`),
                INDEX `idx_style` (`style_id`),
                INDEX `idx_image` (`image_id`),
                FOREIGN KEY (`style_id`) REFERENCES `styles` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风格图片表';
        """)
        print("风格图片表创建成功")
        
        # 3. 创建风格特征画像表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `style_feature_profiles` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `style_id` INT NOT NULL COMMENT '风格ID',
                `feature_id` INT NOT NULL COMMENT '特征ID',
                `feature_name` VARCHAR(100) NOT NULL COMMENT '特征名称',
                `distribution_json` TEXT COMMENT '特征分布JSON，存储每个特征值的数量',
                `is_selected` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否选中进入画像',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY `uk_style_feature` (`style_id`, `feature_id`),
                INDEX `idx_style` (`style_id`),
                INDEX `idx_feature` (`feature_id`),
                INDEX `idx_selected` (`is_selected`),
                FOREIGN KEY (`style_id`) REFERENCES `styles` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`feature_id`) REFERENCES `features` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风格特征画像表';
        """)
        print("风格特征画像表创建成功")
        
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

