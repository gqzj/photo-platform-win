"""
创建图片打标结果历史表
记录每个任务对每个图片每个特征的打标结果
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

def create_table():
    """创建图片打标结果历史表"""
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
        
        # 创建图片打标结果历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `image_tagging_results_history` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `tagging_task_id` INT NOT NULL COMMENT '打标任务ID',
                `image_id` INT NOT NULL COMMENT '图片ID',
                `feature_id` INT NOT NULL COMMENT '特征ID',
                `tagging_value` VARCHAR(500) COMMENT '打标值',
                `source_task_id` INT COMMENT '来源任务ID（如果复用其他任务的结果，记录原始任务ID）',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX `idx_task` (`tagging_task_id`),
                INDEX `idx_image` (`image_id`),
                INDEX `idx_feature` (`feature_id`),
                INDEX `idx_source_task` (`source_task_id`),
                INDEX `idx_image_feature` (`image_id`, `feature_id`),
                FOREIGN KEY (`tagging_task_id`) REFERENCES `tagging_tasks` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`feature_id`) REFERENCES `features` (`id`) ON DELETE CASCADE,
                FOREIGN KEY (`source_task_id`) REFERENCES `tagging_tasks` (`id`) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图片打标结果历史表';
        """)
        
        connection.commit()
        print("图片打标结果历史表创建成功")
        
    except Exception as e:
        print(f"创建表失败: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    create_table()

