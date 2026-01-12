# -*- coding: utf-8 -*-
"""
创建语义搜索相关表的迁移脚本
"""
from app import create_app
from app.database import db
from app.models.semantic_search import SemanticSearchImage

def create_tables():
    """创建表"""
    app = create_app()
    with app.app_context():
        try:
            # 创建表
            db.create_all()
            print("语义搜索表创建成功")
        except Exception as e:
            print(f"创建表失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_tables()
