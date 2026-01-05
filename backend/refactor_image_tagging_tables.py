"""
重构图片打标结果表结构
1. image_tagging_results: 每个图片一行，存储汇总结果
2. image_tagging_results_detail: 每个图片每个特征一行，只记录最后打标任务ID
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    """从环境变量读取数据库配置"""
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'photo_platform')
    }

def refactor_tables():
    """重构表结构"""
    db_config = get_db_config()
    
    connection = None
    try:
        connection = pymysql.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 3306),
            user=db_config.get('user', 'root'),
            password=db_config.get('password', ''),
            database=db_config.get('database', 'photo_platform'),
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 1. 检查并创建新的image_tagging_results_detail表
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'image_tagging_results_detail'
        """, (db_config.get('database', 'photo_platform'),))
        
        detail_table_exists = cursor.fetchone()[0] > 0
        
        if not detail_table_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `image_tagging_results_detail` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                    `image_id` INT NOT NULL COMMENT '图片ID',
                    `feature_id` INT NOT NULL COMMENT '特征ID',
                    `tagging_value` VARCHAR(500) COMMENT '打标值',
                    `last_tagging_task_id` INT COMMENT '最后打标任务ID',
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX `idx_image` (`image_id`),
                    INDEX `idx_feature` (`feature_id`),
                    INDEX `idx_task` (`last_tagging_task_id`),
                    UNIQUE KEY `uk_image_feature` (`image_id`, `feature_id`),
                    FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`feature_id`) REFERENCES `features` (`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`last_tagging_task_id`) REFERENCES `tagging_tasks` (`id`) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片打标结果明细表';
            """)
            print("创建 image_tagging_results_detail 表成功")
        else:
            print("image_tagging_results_detail 表已存在，跳过创建")
        
        # 2. 备份旧表数据（如果需要）
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'image_tagging_results_backup'
        """, (db_config.get('database', 'photo_platform'),))
        
        backup_exists = cursor.fetchone()[0] > 0
        
        if not backup_exists:
            cursor.execute("""
                CREATE TABLE `image_tagging_results_backup` AS 
                SELECT * FROM `image_tagging_results`
            """)
            print("备份旧表数据成功")
        
        # 3. 迁移数据到新表结构
        # 先迁移到detail表：每个图片每个特征的最新记录
        print("开始迁移数据到 image_tagging_results_detail 表...")
        cursor.execute("""
            INSERT INTO `image_tagging_results_detail` (`image_id`, `feature_id`, `tagging_value`, `last_tagging_task_id`, `created_at`, `updated_at`)
            SELECT 
                t1.image_id,
                t1.feature_id,
                t1.tagging_value,
                t1.tagging_task_id,
                t1.created_at,
                t1.updated_at
            FROM `image_tagging_results` t1
            INNER JOIN (
                SELECT image_id, feature_id, MAX(updated_at) as max_updated_at
                FROM `image_tagging_results`
                GROUP BY image_id, feature_id
            ) t2 ON t1.image_id = t2.image_id 
                AND t1.feature_id = t2.feature_id 
                AND t1.updated_at = t2.max_updated_at
            ON DUPLICATE KEY UPDATE
                `tagging_value` = VALUES(`tagging_value`),
                `last_tagging_task_id` = VALUES(`last_tagging_task_id`),
                `updated_at` = VALUES(`updated_at`)
        """)
        print(f"迁移到 detail 表完成，影响行数: {cursor.rowcount}")
        
        # 4. 删除旧表并重建image_tagging_results表（汇总表）
        cursor.execute("DROP TABLE IF EXISTS `image_tagging_results`")
        print("删除旧表成功")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `image_tagging_results` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `image_id` INT NOT NULL COMMENT '图片ID',
                `last_tagging_task_id` INT COMMENT '最后打标任务ID',
                `tagging_result_json` TEXT COMMENT '完整的打标结果JSON（包含所有特征）',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY `uk_image` (`image_id`),
                INDEX `idx_task` (`last_tagging_task_id`),
                FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`last_tagging_task_id`) REFERENCES `tagging_tasks` (`id`) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片打标结果汇总表';
        """)
        print("创建新的 image_tagging_results 汇总表成功")
        
        # 5. 迁移汇总数据到新表
        print("开始迁移汇总数据到 image_tagging_results 表...")
        cursor.execute("""
            INSERT INTO `image_tagging_results` (`image_id`, `last_tagging_task_id`, `tagging_result_json`, `created_at`, `updated_at`)
            SELECT 
                t1.image_id,
                t1.tagging_task_id,
                t1.tagging_result_json,
                MIN(t1.created_at),
                MAX(t1.updated_at)
            FROM `image_tagging_results_backup` t1
            INNER JOIN (
                SELECT image_id, MAX(updated_at) as max_updated_at
                FROM `image_tagging_results_backup`
                GROUP BY image_id
            ) t2 ON t1.image_id = t2.image_id AND t1.updated_at = t2.max_updated_at
            GROUP BY t1.image_id, t1.tagging_task_id, t1.tagging_result_json
        """)
        print(f"迁移汇总数据完成，影响行数: {cursor.rowcount}")
        
        connection.commit()
        print("表结构重构完成！")
        
    except Exception as e:
        print(f"重构表结构失败: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    refactor_tables()

