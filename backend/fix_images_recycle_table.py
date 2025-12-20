# -*- coding: utf-8 -*-
"""修复images_recycle表，删除重复字段"""
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
        columns = inspector.get_columns('images_recycle')
        column_names = [col['name'] for col in columns]
        print(f"现有字段: {column_names}")
        
        if 'origin_image_id' in column_names and 'original_image_id' in column_names:
            print("\n发现重复字段 origin_image_id 和 original_image_id")
            print("准备删除旧的 origin_image_id 字段...")
            try:
                # 删除旧的字段
                db.session.execute(text("ALTER TABLE images_recycle DROP COLUMN origin_image_id"))
                db.session.commit()
                print("成功删除 origin_image_id 字段")
            except Exception as e:
                db.session.rollback()
                print(f"删除字段失败: {e}")
        elif 'origin_image_id' in column_names:
            print("\n发现 origin_image_id 字段，但缺少 original_image_id")
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
            print("\n字段结构正常")
    else:
        print("images_recycle 表不存在")

