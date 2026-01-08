# -*- coding: utf-8 -*-
"""
创建lut_cluster_snapshots表
用于存储LUT聚类分析快照
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import text

def create_table():
    """创建表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'lut_cluster_snapshots' in tables:
                print("表 lut_cluster_snapshots 已存在，跳过")
                return
            
            # 创建表
            print("正在创建 lut_cluster_snapshots 表...")
            db.session.execute(text("""
                CREATE TABLE lut_cluster_snapshots (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                    name VARCHAR(200) NOT NULL COMMENT '快照名称',
                    description TEXT COMMENT '快照描述',
                    metric VARCHAR(50) NOT NULL COMMENT '聚类指标',
                    metric_name VARCHAR(100) COMMENT '聚类指标名称',
                    algorithm VARCHAR(50) NOT NULL COMMENT '聚类算法',
                    algorithm_name VARCHAR(100) COMMENT '聚类算法名称',
                    n_clusters INT NOT NULL COMMENT '聚类数',
                    cluster_data_json TEXT COMMENT '聚类数据JSON（包含每个聚类的文件列表和统计信息）',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LUT聚类快照表'
            """))
            db.session.commit()
            print("表创建成功")
            
        except Exception as e:
            db.session.rollback()
            print(f"创建表失败: {e}")
            raise

if __name__ == '__main__':
    create_table()
