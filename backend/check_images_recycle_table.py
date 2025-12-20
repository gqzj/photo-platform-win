# -*- coding: utf-8 -*-
"""检查images_recycle表结构"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    
    if inspector.has_table('images_recycle'):
        print("images_recycle 表结构:")
        columns = inspector.get_columns('images_recycle')
        column_names = [col['name'] for col in columns]
        print(f"现有字段: {column_names}")
        
        if 'original_image_id' not in column_names:
            if 'origin_image_id' in column_names:
                print("\n发现 origin_image_id 字段，但模型使用 original_image_id")
                print("准备重命名字段...")
                try:
                    # 重命名字段
                    db.session.execute(text("ALTER TABLE images_recycle CHANGE COLUMN origin_image_id original_image_id INT COMMENT '原图片ID'"))
                    db.session.commit()
                    print("成功重命名 origin_image_id 为 original_image_id")
                except Exception as e:
                    db.session.rollback()
                    print(f"重命名字段失败: {e}")
            else:
                print("\n缺少 original_image_id 字段，准备添加...")
                try:
                    # 添加缺失的字段
                    db.session.execute(text("ALTER TABLE images_recycle ADD COLUMN original_image_id INT COMMENT '原图片ID'"))
                    db.session.commit()
                    print("成功添加 original_image_id 字段")
                except Exception as e:
                    db.session.rollback()
                    print(f"添加字段失败: {e}")
        else:
            print("\noriginal_image_id 字段已存在")
    else:
        print("images_recycle 表不存在")

