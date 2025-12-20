# -*- coding: utf-8 -*-
"""创建数据打标任务表"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.tagging_task import TaggingTask

app = create_app()

with app.app_context():
    try:
        # 创建表
        db.create_all()
        print("数据打标任务表创建成功！")
        
        # 验证表是否存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'tagging_tasks' in tables:
            print("验证：tagging_tasks 表已存在")
            
            # 显示表结构
            columns = inspector.get_columns('tagging_tasks')
            print("\n表结构：")
            for col in columns:
                print(f"  {col['name']}: {col['type']}")
        else:
            print("警告：tagging_tasks 表不存在")
            
    except Exception as e:
        print(f"创建表失败: {e}")
        import traceback
        traceback.print_exc()

