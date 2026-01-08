# -*- coding: utf-8 -*-
"""
为lut_clusters表添加distance_to_center字段
用于存储LUT文件到聚类中心的距离
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import text

def add_distance_to_center_field():
    """添加distance_to_center字段"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('lut_clusters')]
            
            if 'distance_to_center' in columns:
                print("字段 distance_to_center 已存在，跳过")
                return
            
            # 添加字段
            print("正在添加 distance_to_center 字段...")
            db.session.execute(text("""
                ALTER TABLE lut_clusters 
                ADD COLUMN distance_to_center FLOAT NULL 
                COMMENT '到聚类中心的距离'
            """))
            db.session.commit()
            print("字段添加成功")
            
        except Exception as e:
            db.session.rollback()
            print(f"添加字段失败: {e}")
            raise

if __name__ == '__main__':
    add_distance_to_center_field()
