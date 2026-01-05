"""
创建需求任务关联表
记录需求关联的任务和执行顺序
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
    """创建需求任务关联表"""
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
        
        # 创建需求任务关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `requirement_tasks` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                `requirement_id` INT NOT NULL COMMENT '需求ID',
                `task_type` VARCHAR(50) NOT NULL COMMENT '任务类型：crawler(抓取), cleaning(清洗), tagging(打标), sample_set(样本集)',
                `task_id` INT NOT NULL COMMENT '任务ID',
                `task_order` INT NOT NULL COMMENT '任务顺序（1,2,3...）',
                `status` VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '状态：pending(待执行), running(执行中), completed(已完成), failed(失败)',
                `started_at` DATETIME COMMENT '开始时间',
                `finished_at` DATETIME COMMENT '完成时间',
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_requirement` (`requirement_id`),
                INDEX `idx_task_type` (`task_type`),
                INDEX `idx_status` (`status`),
                INDEX `idx_order` (`requirement_id`, `task_order`),
                FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求任务关联表';
        """)
        
        connection.commit()
        print("需求任务关联表创建成功")
        
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

