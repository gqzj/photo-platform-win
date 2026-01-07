# -*- coding: utf-8 -*-
"""
为LUT文件分析任务表添加interrupted字段
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

def add_field():
    """添加字段"""
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
            # 检查字段是否已存在
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'lut_file_analysis_tasks' 
                AND COLUMN_NAME = 'interrupted'
            """, (os.getenv('MYSQL_DATABASE', 'photo_platform'),))
            
            if cursor.fetchone()[0] > 0:
                print("✓ 字段 `interrupted` 已存在，跳过")
                return
            
            # 添加字段
            sql = """
            ALTER TABLE `lut_file_analysis_tasks` 
            ADD COLUMN `interrupted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否被中断：0-否，1-是' AFTER `failed_count`;
            """
            
            cursor.execute(sql)
            connection.commit()
            print("✓ 字段 `interrupted` 添加成功")
            
    except Exception as e:
        print(f"✗ 添加字段失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("开始添加interrupted字段...")
    add_field()
    print("完成！")

