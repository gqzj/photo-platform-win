# -*- coding: utf-8 -*-
"""
为lut_clusters表添加parent_cluster_id字段
用于支持层级聚类（再次聚类功能）
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import text

def add_parent_cluster_id_field():
    """添加parent_cluster_id字段"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('lut_clusters')]
            
            if 'parent_cluster_id' in columns:
                print("字段 parent_cluster_id 已存在，跳过")
                return
            
            # 添加字段
            print("正在添加 parent_cluster_id 字段...")
            db.session.execute(text("""
                ALTER TABLE lut_clusters 
                ADD COLUMN parent_cluster_id INT NULL 
                COMMENT '父聚类ID（NULL表示顶级聚类）'
            """))
            
            # 添加索引
            print("正在添加索引...")
            db.session.execute(text("""
                ALTER TABLE lut_clusters 
                ADD INDEX idx_parent_cluster_id (parent_cluster_id)
            """))
            
            db.session.commit()
            print("字段和索引添加成功")
            
        except Exception as e:
            db.session.rollback()
            print(f"添加字段失败: {e}")
            raise

if __name__ == '__main__':
    add_parent_cluster_id_field()
