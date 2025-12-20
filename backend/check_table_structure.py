"""检查crawler_cookies表的结构"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import inspect, text

def check_table_structure():
    """检查表结构"""
    app = create_app()
    with app.app_context():
        try:
            # 获取表结构
            inspector = inspect(db.engine)
            
            # 检查表是否存在
            tables = inspector.get_table_names()
            if 'crawler_cookies' not in tables:
                print("crawler_cookies 表不存在")
                return
            
            print("=" * 50)
            print("crawler_cookies 表结构:")
            print("=" * 50)
            
            # 获取列信息
            columns = inspector.get_columns('crawler_cookies')
            for col in columns:
                print(f"{col['name']}: {col['type']} (nullable: {col.get('nullable', True)})")
            
            print("\n" + "=" * 50)
            print("模型定义的字段:")
            print("=" * 50)
            from app.models.crawler_cookie import CrawlerCookie
            for column in CrawlerCookie.__table__.columns:
                print(f"{column.name}: {column.type} (nullable: {column.nullable})")
            
        except Exception as e:
            print(f"检查失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_table_structure()

