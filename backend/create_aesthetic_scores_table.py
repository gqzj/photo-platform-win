# -*- coding: utf-8 -*-
"""
创建美学评分表
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_table():
    """创建美学评分表"""
    connection = None
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'photo_platform'),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建美学评分表
            sql = """
            CREATE TABLE IF NOT EXISTS `aesthetic_scores` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `style_id` INT NOT NULL COMMENT '风格ID',
                `image_id` INT NOT NULL COMMENT '图片ID',
                `evaluator_type` VARCHAR(50) NOT NULL COMMENT '评分器类型：artimuse, q_insight',
                `score` DECIMAL(10, 4) COMMENT '美学评分分数',
                `details_json` TEXT COMMENT '接口返回的详细信息JSON',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_style_image` (`style_id`, `image_id`),
                INDEX `idx_evaluator_type` (`evaluator_type`),
                FOREIGN KEY (`style_id`) REFERENCES `styles` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE,
                UNIQUE KEY `uk_style_image_evaluator` (`style_id`, `image_id`, `evaluator_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='美学评分表';
            """
            cursor.execute(sql)
            print("美学评分表创建成功")
            
            connection.commit()
            
    except Exception as e:
        print(f"创建表失败: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    create_table()

