# -*- coding: utf-8 -*-
"""
创建LUT应用相关的数据表
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    """创建LUT应用相关的数据表"""
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
        # 创建lut_applications表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `lut_applications` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `sample_image_id` INT NOT NULL COMMENT '样本图片ID',
                `status` VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '状态：pending, running, completed, failed',
                `total_lut_count` INT DEFAULT 0 COMMENT '总LUT数量',
                `processed_lut_count` INT DEFAULT 0 COMMENT '已处理LUT数量',
                `error_message` TEXT COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                `finished_at` DATETIME COMMENT '完成时间',
                KEY `idx_sample_image_id` (`sample_image_id`),
                KEY `idx_status` (`status`),
                CONSTRAINT `fk_lut_applications_sample_image` FOREIGN KEY (`sample_image_id`) REFERENCES `sample_images` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LUT应用任务表';
        """)
        print("创建 lut_applications 表成功")
        
        # 创建lut_applied_images表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `lut_applied_images` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `lut_application_id` INT NOT NULL COMMENT 'LUT应用任务ID',
                `lut_file_id` INT NOT NULL COMMENT 'LUT文件ID',
                `sample_image_id` INT NOT NULL COMMENT '样本图片ID',
                `filename` VARCHAR(255) NOT NULL COMMENT '文件名',
                `storage_path` VARCHAR(500) NOT NULL COMMENT '存储路径',
                `file_size` BIGINT COMMENT '文件大小（字节）',
                `width` INT COMMENT '图片宽度',
                `height` INT COMMENT '图片高度',
                `format` VARCHAR(20) COMMENT '图片格式',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                KEY `idx_lut_application_id` (`lut_application_id`),
                KEY `idx_lut_file_id` (`lut_file_id`),
                KEY `idx_sample_image_id` (`sample_image_id`),
                CONSTRAINT `fk_lut_applied_images_application` FOREIGN KEY (`lut_application_id`) REFERENCES `lut_applications` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_lut_applied_images_lut_file` FOREIGN KEY (`lut_file_id`) REFERENCES `lut_files` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_lut_applied_images_sample_image` FOREIGN KEY (`sample_image_id`) REFERENCES `sample_images` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LUT应用后的图片表';
        """)
        print("创建 lut_applied_images 表成功")
        
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

