# -*- coding: utf-8 -*-
"""
创建Lut相关的数据表
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    """创建Lut相关的数据表"""
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
        # 创建lut_categories表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `lut_categories` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `name` VARCHAR(100) NOT NULL COMMENT '分类名称',
                `description` TEXT COMMENT '分类描述',
                `sort_order` INT DEFAULT 0 COMMENT '排序顺序',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY `uk_name` (`name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Lut分类表';
        """)
        print("创建 lut_categories 表成功")
        
        # 创建lut_files表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `lut_files` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `category_id` INT COMMENT '分类ID',
                `filename` VARCHAR(255) NOT NULL COMMENT '文件名',
                `original_filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
                `storage_path` VARCHAR(500) NOT NULL COMMENT '存储路径',
                `file_size` BIGINT COMMENT '文件大小（字节）',
                `file_hash` VARCHAR(128) COMMENT '文件哈希值',
                `description` TEXT COMMENT '文件描述',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                KEY `idx_category_id` (`category_id`),
                KEY `idx_filename` (`filename`),
                CONSTRAINT `fk_lut_files_category` FOREIGN KEY (`category_id`) REFERENCES `lut_categories` (`id`) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Lut文件表';
        """)
        print("创建 lut_files 表成功")
        
        # 创建sample_images表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `sample_images` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `filename` VARCHAR(255) NOT NULL COMMENT '文件名',
                `original_filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
                `storage_path` VARCHAR(500) NOT NULL COMMENT '存储路径',
                `file_size` BIGINT COMMENT '文件大小（字节）',
                `file_hash` VARCHAR(128) COMMENT '文件哈希值',
                `width` INT COMMENT '图片宽度',
                `height` INT COMMENT '图片高度',
                `format` VARCHAR(20) COMMENT '图片格式',
                `description` TEXT COMMENT '图片描述',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                KEY `idx_filename` (`filename`),
                KEY `idx_file_hash` (`file_hash`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='样本图片表';
        """)
        print("创建 sample_images 表成功")
        
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

