# -*- coding: utf-8 -*-
"""
创建LUT文件标签表
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
            CREATE TABLE IF NOT EXISTS `lut_file_tags` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `lut_file_id` INT NOT NULL COMMENT 'LUT文件ID',
                `tone` VARCHAR(50) COMMENT '色调：暖调、冷调、中性调',
                `saturation` VARCHAR(50) COMMENT '饱和度：高饱和、中饱和、低饱和',
                `contrast` VARCHAR(50) COMMENT '对比度：高对比、中对比、低对比',
                `h_mean` DECIMAL(10, 4) COMMENT '色调均值',
                `s_mean` DECIMAL(10, 4) COMMENT '饱和度均值',
                `s_var` DECIMAL(10, 4) COMMENT '饱和度方差',
                `v_var` DECIMAL(10, 4) COMMENT '明度方差',
                `contrast_rgb` DECIMAL(10, 4) COMMENT 'RGB对比度',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                CONSTRAINT `fk_lut_file_tag_lut_file` FOREIGN KEY (`lut_file_id`) REFERENCES `lut_files` (`id`) ON DELETE CASCADE,
                CONSTRAINT `uk_lut_file_tag` UNIQUE (`lut_file_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LUT文件标签表';
            """
            
            cursor.execute(sql)
            connection.commit()
            print("✓ 表 `lut_file_tags` 创建成功")
            
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("开始创建LUT文件标签表...")
    create_table()
    print("完成！")

