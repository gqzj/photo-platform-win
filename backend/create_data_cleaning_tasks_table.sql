-- MySQL 创建数据清洗任务表
CREATE TABLE IF NOT EXISTS `data_cleaning_tasks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(200) NOT NULL COMMENT '任务名称',
    `filter_features` TEXT COMMENT '筛选特征JSON',
    `filter_keywords` TEXT COMMENT '筛选范围关键字JSON',
    `status` VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '状态：pending, running, paused, completed, failed',
    `processed_count` INT NOT NULL DEFAULT 0 COMMENT '任务处理总数',
    `note` TEXT COMMENT '备注',
    `last_error` TEXT COMMENT '最后错误信息',
    `started_at` DATETIME COMMENT '开始时间',
    `finished_at` DATETIME COMMENT '完成时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据清洗任务表';

