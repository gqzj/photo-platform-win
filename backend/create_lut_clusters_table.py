# -*- coding: utf-8 -*-
"""
创建LUT聚类表
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models.lut_cluster import LutCluster

def create_table():
    """创建LUT聚类表"""
    app = create_app()
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            if 'lut_clusters' in inspector.get_table_names():
                print("表 'lut_clusters' 已存在，跳过创建")
                return
            
            # 创建表
            LutCluster.__table__.create(db.engine)
            print("表 'lut_clusters' 创建成功")
        except Exception as e:
            print(f"创建表失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_table()

