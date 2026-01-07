# -*- coding: utf-8 -*-
"""
创建LUT应用后图片美学评分任务表
"""
import sys
import os
import pymysql
from dotenv import load_dotenv

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()

def create_table():
    """创建表"""
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
            # 创建表
            sql = """
            CREATE TABLE IF NOT EXISTS `lut_applied_image_aesthetic_score_tasks` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `sample_image_id` INT NOT NULL COMMENT '样本图片ID',
                `status` VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '状态：pending, running, completed, failed',
                `evaluator_type` VARCHAR(50) NOT NULL COMMENT '评分器类型：artimuse, q_insight',
                `score_mode` VARCHAR(50) NOT NULL DEFAULT 'score_and_reason' COMMENT '评分模式：score_only, score_and_reason',
                `total_image_count` INT DEFAULT 0 COMMENT '总图片数量',
                `processed_image_count` INT DEFAULT 0 COMMENT '已处理图片数量',
                `error_message` TEXT COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                `finished_at` DATETIME COMMENT '完成时间',
                CONSTRAINT `fk_lut_applied_image_aesthetic_score_task_sample_image` FOREIGN KEY (`sample_image_id`) REFERENCES `sample_images` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LUT应用后图片美学评分任务表';
            """
            
            cursor.execute(sql)
            connection.commit()
            print("✓ 表 `lut_applied_image_aesthetic_score_tasks` 创建成功")
            
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("开始创建LUT应用后图片美学评分任务表...")
    create_table()
    print("完成！")

