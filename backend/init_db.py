"""
数据库初始化脚本
用于创建数据库表
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_cookie import CrawlerCookie
from app.models.image import Image

def init_db():
    """初始化数据库表"""
    app = create_app()
    with app.app_context():
        try:
            # 创建所有表
            db.create_all()
            print("✓ 数据库表创建成功")
            
            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✓ 当前数据库中的表: {', '.join(tables)}")
            
            # 检查 crawler_cookies 表
            if 'crawler_cookies' in tables:
                print("✓ crawler_cookies 表已存在")
            else:
                print("✗ crawler_cookies 表不存在")
                
        except Exception as e:
            print(f"✗ 数据库初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("开始初始化数据库...")
    if init_db():
        print("\n数据库初始化完成！")
    else:
        print("\n数据库初始化失败！")
        sys.exit(1)
