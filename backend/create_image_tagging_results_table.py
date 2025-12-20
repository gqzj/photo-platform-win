# -*- coding: utf-8 -*-
"""
创建图片打标结果表
"""
import pymysql
import json
import os
from dotenv import load_dotenv

load_dotenv()

def create_table():
    """创建图片打标结果表"""
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
            # 创建图片打标结果表
            sql = """
            CREATE TABLE IF NOT EXISTS `image_tagging_results` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `tagging_task_id` INT NOT NULL COMMENT '打标任务ID',
                `image_id` INT NOT NULL COMMENT '图片ID',
                `feature_id` INT NOT NULL COMMENT '特征ID',
                `tagging_value` VARCHAR(500) COMMENT '打标值（单个特征的值）',
                `tagging_result_json` TEXT COMMENT '完整的打标结果JSON（包含所有特征）',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_task_image` (`tagging_task_id`, `image_id`),
                INDEX `idx_image` (`image_id`),
                INDEX `idx_feature` (`feature_id`),
                UNIQUE KEY `uk_task_image_feature` (`tagging_task_id`, `image_id`, `feature_id`),
                FOREIGN KEY (`tagging_task_id`) REFERENCES `tagging_tasks` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`feature_id`) REFERENCES `features` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片打标结果表';
            """
            
            cursor.execute(sql)
            connection.commit()
            print("图片打标结果表创建成功")
            
    except Exception as e:
        print(f"创建表失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    create_table()

