# -*- coding: utf-8 -*-
"""
创建LUT文件分析任务表
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
            CREATE TABLE IF NOT EXISTS `lut_file_analysis_tasks` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `status` VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '状态：pending, running, completed, failed',
                `total_file_count` INT DEFAULT 0 COMMENT '总文件数量',
                `processed_file_count` INT DEFAULT 0 COMMENT '已处理文件数量',
                `success_count` INT DEFAULT 0 COMMENT '成功数量',
                `failed_count` INT DEFAULT 0 COMMENT '失败数量',
                `error_message` TEXT COMMENT '错误信息',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                `finished_at` DATETIME COMMENT '完成时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LUT文件分析任务表';
            """
            
            cursor.execute(sql)
            connection.commit()
            print("✓ 表 `lut_file_analysis_tasks` 创建成功")
            
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("开始创建LUT文件分析任务表...")
    create_table()
    print("完成！")

