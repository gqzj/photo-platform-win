# -*- coding: utf-8 -*-
"""
创建LUT应用后图片美学评分表
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
            CREATE TABLE IF NOT EXISTS `lut_applied_image_aesthetic_scores` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `lut_applied_image_id` INT NOT NULL COMMENT 'LUT应用后图片ID',
                `evaluator_type` VARCHAR(50) NOT NULL COMMENT '评分器类型：artimuse, q_insight',
                `score` DECIMAL(10, 4) COMMENT '美学评分分数',
                `details_json` TEXT COMMENT '接口返回的详细信息JSON',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                CONSTRAINT `fk_lut_applied_image_aesthetic_score` FOREIGN KEY (`lut_applied_image_id`) REFERENCES `lut_applied_images` (`id`) ON DELETE CASCADE,
                CONSTRAINT `uk_lut_applied_image_evaluator` UNIQUE (`lut_applied_image_id`, `evaluator_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LUT应用后图片美学评分表';
            """
            
            cursor.execute(sql)
            connection.commit()
            print("✓ 表 `lut_applied_image_aesthetic_scores` 创建成功")
            
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("开始创建LUT应用后图片美学评分表...")
    create_table()
    print("完成！")

