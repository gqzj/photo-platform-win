"""
测试数据库连接
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_cookie import CrawlerCookie

def test_connection():
    """测试数据库连接"""
    app = create_app()
    with app.app_context():
        try:
            # 测试连接
            db.engine.connect()
            print("数据库连接成功")
            
            # 测试查询表
            try:
                count = CrawlerCookie.query.count()
                print(f"crawler_cookies 表查询成功，当前记录数: {count}")
            except Exception as e:
                print(f"✗ crawler_cookies 表查询失败: {str(e)}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            error_msg = str(e)
            print(f"数据库连接失败: {error_msg}")
            if "Access denied" in error_msg:
                print("\n提示: 数据库需要密码，请在 backend/.env 文件中配置 MYSQL_PASSWORD")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("开始测试数据库连接...")
    print(f"数据库URI: {os.getenv('MYSQL_DATABASE', 'photo_platform')}")
    print(f"数据库主机: {os.getenv('MYSQL_HOST', 'localhost')}")
    print(f"数据库用户: {os.getenv('MYSQL_USER', 'root')}")
    print(f"数据库密码: {'已设置' if os.getenv('MYSQL_PASSWORD') else '未设置'}")
    print("-" * 50)
    
    if test_connection():
        print("\n数据库连接测试完成！")
    else:
        print("\n数据库连接测试失败！")
        print("\n请检查：")
        print("1. 数据库服务是否运行")
        print("2. 数据库连接配置是否正确（backend/.env 文件）")
        print("3. 数据库用户权限是否正确")
        sys.exit(1)

