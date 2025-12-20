# -*- coding: utf-8 -*-
"""
创建样本集相关表
"""
import pymysql
import json
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    """创建样本集相关表"""
    # 数据库连接配置
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'photo_platform'),
        'charset': 'utf8mb4'
    }
    
    connection = pymysql.connect(**config)
    
    try:
        with connection.cursor() as cursor:
            # 1. 创建样本集表
            sql1 = """
            CREATE TABLE IF NOT EXISTS `sample_sets` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `name` VARCHAR(200) NOT NULL COMMENT '样本集名称',
                `description` TEXT COMMENT '样本集描述',
                `status` VARCHAR(50) NOT NULL DEFAULT 'active' COMMENT '状态：active, inactive',
                `image_count` INT NOT NULL DEFAULT 0 COMMENT '图片数量',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_status` (`status`),
                INDEX `idx_name` (`name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='样本集表';
            """
            cursor.execute(sql1)
            print("样本集表创建成功")
            
            # 2. 创建样本集特征表
            sql2 = """
            CREATE TABLE IF NOT EXISTS `sample_set_features` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `sample_set_id` INT NOT NULL COMMENT '样本集ID',
                `feature_id` INT NOT NULL COMMENT '特征ID',
                `feature_name` VARCHAR(100) NOT NULL COMMENT '特征名称',
                `value_range` TEXT COMMENT '特征取值范围JSON，例如：["值1", "值2"] 或 {"min": 1, "max": 10}',
                `value_type` VARCHAR(50) NOT NULL DEFAULT 'enum' COMMENT '值类型：enum(枚举), range(范围), any(任意)',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_sample_set` (`sample_set_id`),
                INDEX `idx_feature` (`feature_id`),
                FOREIGN KEY (`sample_set_id`) REFERENCES `sample_sets` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`feature_id`) REFERENCES `features` (`id`) ON DELETE CASCADE,
                UNIQUE KEY `uk_sample_set_feature` (`sample_set_id`, `feature_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='样本集特征表';
            """
            cursor.execute(sql2)
            print("样本集特征表创建成功")
            
            # 3. 创建样本集图片表
            sql3 = """
            CREATE TABLE IF NOT EXISTS `sample_set_images` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `sample_set_id` INT NOT NULL COMMENT '样本集ID',
                `image_id` INT NOT NULL COMMENT '图片ID',
                `matched_features` TEXT COMMENT '匹配的特征JSON，记录哪些特征匹配',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX `idx_sample_set` (`sample_set_id`),
                INDEX `idx_image` (`image_id`),
                FOREIGN KEY (`sample_set_id`) REFERENCES `sample_sets` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE,
                UNIQUE KEY `uk_sample_set_image` (`sample_set_id`, `image_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='样本集图片表';
            """
            cursor.execute(sql3)
            print("样本集图片表创建成功")
            
            connection.commit()
            print("所有表创建成功")
            
    except Exception as e:
        print(f"创建表失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    create_tables()

