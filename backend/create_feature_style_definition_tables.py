# -*- coding: utf-8 -*-
"""
创建特征风格定义相关表
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
    """创建特征风格定义相关表"""
    config = get_db_config()
    connection = None
    
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 1. 创建特征风格定义表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `feature_style_definitions` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `name` VARCHAR(200) NOT NULL UNIQUE COMMENT '风格定义名称',
                `description` TEXT COMMENT '风格定义描述',
                `dimensions_json` TEXT COMMENT '维度定义JSON',
                `status` VARCHAR(50) NOT NULL DEFAULT 'active' COMMENT '状态：active, inactive',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_status` (`status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='特征风格定义表';
        """)
        print("特征风格定义表创建成功")
        
        # 2. 创建特征风格子风格表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `feature_style_sub_styles` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `feature_style_definition_id` INT NOT NULL COMMENT '特征风格定义ID',
                `name` VARCHAR(200) NOT NULL COMMENT '子风格名称',
                `dimension_values_json` TEXT COMMENT '维度值组合JSON',
                `description` TEXT COMMENT '子风格描述',
                `image_count` INT NOT NULL DEFAULT 0 COMMENT '图片数量',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY `uk_feature_style_sub_style` (`feature_style_definition_id`, `name`),
                INDEX `idx_feature_style_definition` (`feature_style_definition_id`),
                FOREIGN KEY (`feature_style_definition_id`) REFERENCES `feature_style_definitions` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='特征风格子风格表';
        """)
        print("特征风格子风格表创建成功")
        
        # 3. 创建特征风格子风格图片表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `feature_style_sub_style_images` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `sub_style_id` INT NOT NULL COMMENT '子风格ID',
                `image_id` INT NOT NULL COMMENT '图片ID',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                UNIQUE KEY `uk_sub_style_image` (`sub_style_id`, `image_id`),
                INDEX `idx_sub_style` (`sub_style_id`),
                INDEX `idx_image` (`image_id`),
                FOREIGN KEY (`sub_style_id`) REFERENCES `feature_style_sub_styles` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='特征风格子风格图片表';
        """)
        print("特征风格子风格图片表创建成功")
        
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
