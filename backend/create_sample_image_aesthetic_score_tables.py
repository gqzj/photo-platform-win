# -*- coding: utf-8 -*-
"""
创建样本图片美学评分相关的数据表
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    """创建样本图片美学评分相关的数据表"""
    # 数据库连接配置
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = int(os.getenv('MYSQL_PORT', 3306))
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'photo_platform')
    
    # 连接数据库
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    try:
        # 创建sample_image_aesthetic_scores表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `sample_image_aesthetic_scores` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `sample_image_id` INT NOT NULL COMMENT '样本图片ID',
                `evaluator_type` VARCHAR(50) NOT NULL COMMENT '评分器类型：artimuse, q_insight',
                `score` DECIMAL(10, 4) COMMENT '美学评分分数',
                `details_json` TEXT COMMENT '接口返回的详细信息JSON',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_sample_image_id` (`sample_image_id`),
                INDEX `idx_evaluator_type` (`evaluator_type`),
                FOREIGN KEY (`sample_image_id`) REFERENCES `sample_images` (`id`) ON DELETE CASCADE,
                UNIQUE KEY `uk_sample_image_evaluator` (`sample_image_id`, `evaluator_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='样本图片美学评分表';
        """)
        print("创建 sample_image_aesthetic_scores 表成功")
        
        # 创建sample_image_aesthetic_score_tasks表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `sample_image_aesthetic_score_tasks` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `status` VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '状态：pending, running, completed, failed',
                `evaluator_type` VARCHAR(50) NOT NULL COMMENT '评分器类型：artimuse, q_insight',
                `score_mode` VARCHAR(50) NOT NULL DEFAULT 'score_and_reason' COMMENT '评分模式：score_only, score_and_reason',
                `total_image_count` INT DEFAULT 0 COMMENT '总图片数量',
                `processed_image_count` INT DEFAULT 0 COMMENT '已处理图片数量',
                `error_message` TEXT COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                `finished_at` DATETIME COMMENT '完成时间',
                INDEX `idx_status` (`status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='样本图片美学评分任务表';
        """)
        print("创建 sample_image_aesthetic_score_tasks 表成功")
        
        # 提交事务
        conn.commit()
        print("\n所有表创建成功！")
        
    except Exception as e:
        conn.rollback()
        print(f"创建表失败: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_tables()

