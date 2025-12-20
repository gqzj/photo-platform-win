"""检查crawler_tasks表结构"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import inspect

def check_table_structure():
    """检查表结构"""
    app = create_app()
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            if 'crawler_tasks' in inspector.get_table_names():
                print("=" * 50)
                print("crawler_tasks 表结构:")
                print("=" * 50)
                columns = inspector.get_columns('crawler_tasks')
                for col in columns:
                    nullable = col.get('nullable', True)
                    default = col.get('default', None)
                    print(f"{col['name']}: {col['type']} (nullable: {nullable}, default: {default})")
            else:
                print("crawler_tasks 表不存在")
            
        except Exception as e:
            print(f"检查失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_table_structure()

