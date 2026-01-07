# -*- coding: utf-8 -*-
"""
给lut_files表添加thumbnail_path字段
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db

def add_column():
    """添加thumbnail_path字段"""
    app = create_app()
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('lut_files')]
            
            if 'thumbnail_path' in columns:
                print("字段 'thumbnail_path' 已存在，跳过添加")
                return
            
            # 添加字段
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE lut_files ADD COLUMN thumbnail_path VARCHAR(500) COMMENT '缩略图路径'"))
                conn.commit()
            
            print("字段 'thumbnail_path' 添加成功")
        except Exception as e:
            print(f"添加字段失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    add_column()

