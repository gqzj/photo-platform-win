# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print("数据库中的所有表:")
    for table in tables:
        print(f"  - {table}")
    
    print("\n" + "=" * 60)
    
    if 'features' in tables:
        print("features 表结构:")
        columns = inspector.get_columns('features')
        for col in columns:
            print(f"  字段名: {col['name']}")
            print(f"  类型: {col['type']}")
            print(f"  可空: {col.get('nullable', True)}")
            print(f"  默认值: {col.get('default', None)}")
            print()
        
        # 获取主键
        pk_constraint = inspector.get_pk_constraint('features')
        if pk_constraint:
            print(f"主键: {pk_constraint['constrained_columns']}")
        
        # 获取唯一约束
        unique_constraints = inspector.get_unique_constraints('features')
        if unique_constraints:
            print("\n唯一约束:")
            for uc in unique_constraints:
                print(f"  {uc['name']}: {uc['column_names']}")
    else:
        print("features 表不存在")

