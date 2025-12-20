# -*- coding: utf-8 -*-
"""
创建关键字统计表
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_table():
    """创建关键字统计表"""
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
            # 创建关键字统计表
            sql = """
            CREATE TABLE IF NOT EXISTS `keyword_statistics` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `keyword` VARCHAR(500) NOT NULL UNIQUE COMMENT '关键字名称',
                `image_count` INT NOT NULL DEFAULT 0 COMMENT '图片总数',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_keyword` (`keyword`),
                INDEX `idx_image_count` (`image_count`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键字统计表';
            """
            cursor.execute(sql)
            connection.commit()
            print("[成功] 关键字统计表创建成功")
            
            # 初始化数据：从images表中统计关键字
            print("[信息] 开始初始化关键字统计数据...")
            cursor.execute("""
                INSERT INTO `keyword_statistics` (`keyword`, `image_count`)
                SELECT `keyword`, COUNT(*) as `image_count`
                FROM `images`
                WHERE `keyword` IS NOT NULL AND `keyword` != ''
                GROUP BY `keyword`
                ON DUPLICATE KEY UPDATE 
                    `image_count` = VALUES(`image_count`),
                    `updated_at` = CURRENT_TIMESTAMP
            """)
            connection.commit()
            print("[成功] 关键字统计数据初始化完成")
                
    except Exception as e:
        print(f"创建表失败: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    create_table()

