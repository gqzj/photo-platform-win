"""详细测试API，包含错误追踪"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_task import CrawlerTask

app = create_app()

print("=" * 60)
print("详细API测试")
print("=" * 60)

# 测试数据库连接和查询
print("\n1. 测试数据库连接和查询")
print("-" * 60)

try:
    with app.app_context():
        print("创建应用上下文...")
        
        print("查询任务总数...")
        total = CrawlerTask.query.count()
        print(f"[OK] 任务总数: {total}")
        
        if total > 0:
            print("\n查询前3条任务...")
            tasks = CrawlerTask.query.limit(3).all()
            print(f"[OK] 查询到 {len(tasks)} 条任务")
            
            print("\n测试to_dict()方法...")
            for i, task in enumerate(tasks, 1):
                try:
                    task_dict = task.to_dict()
                    print(f"[OK] 任务 {i} to_dict() 成功")
                    print(f"  字段数量: {len(task_dict)}")
                except Exception as e:
                    print(f"[ERROR] 任务 {i} to_dict() 失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
except Exception as e:
    print(f"[ERROR] 数据库查询失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试API路由
print("\n2. 测试API路由处理")
print("-" * 60)

try:
    with app.test_client() as client:
        print("创建测试客户端...")
        
        print("发送GET请求到 /api/crawler/tasks...")
        response = client.get('/api/crawler/tasks?page=1&page_size=10')
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ API请求成功")
            data = response.get_json()
            print(f"  响应code: {data.get('code')}")
            print(f"  响应message: {data.get('message')}")
            if 'data' in data:
                print(f"  数据总数: {data['data'].get('total')}")
                print(f"  列表长度: {len(data['data'].get('list', []))}")
        else:
            print(f"✗ API请求失败，状态码: {response.status_code}")
            try:
                error_data = response.get_json()
                print(f"  错误响应: {error_data}")
            except:
                error_text = response.get_data(as_text=True)
                print(f"  错误文本: {error_text[:500]}")
                
except Exception as e:
    print(f"[ERROR] API测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")

