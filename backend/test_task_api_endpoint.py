"""测试任务API接口"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import json

app = create_app()

print("=" * 60)
print("测试任务列表API接口")
print("=" * 60)

with app.test_client() as client:
    try:
        print("\n1. 测试 GET /api/crawler/tasks?page=1&page_size=10")
        print("-" * 60)
        
        response = client.get('/api/crawler/tasks?page=1&page_size=10')
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"\n响应数据:")
            print(f"  code: {data.get('code')}")
            print(f"  message: {data.get('message')}")
            if 'data' in data:
                print(f"  data.total: {data['data'].get('total')}")
                print(f"  data.page: {data['data'].get('page')}")
                print(f"  data.page_size: {data['data'].get('page_size')}")
                print(f"  data.list 长度: {len(data['data'].get('list', []))}")
                if data['data'].get('list'):
                    print(f"\n第一条任务数据:")
                    task = data['data']['list'][0]
                    for key, value in task.items():
                        print(f"    {key}: {value}")
        else:
            print(f"\n错误响应:")
            try:
                error_data = response.get_json()
                print(f"  JSON响应: {error_data}")
            except:
                print(f"  文本响应: {response.get_data(as_text=True)[:500]}")
        
        print("\n" + "=" * 60)
        print("2. 测试数据库直接查询")
        print("-" * 60)
        
        from app.database import db
        from app.models.crawler_task import CrawlerTask
        
        with app.app_context():
            total = CrawlerTask.query.count()
            print(f"数据库中的任务总数: {total}")
            
            if total > 0:
                tasks = CrawlerTask.query.limit(3).all()
                print(f"\n前3条任务:")
                for i, task in enumerate(tasks, 1):
                    print(f"\n任务 {i}:")
                    try:
                        task_dict = task.to_dict()
                        print(f"  ID: {task_dict.get('id')}")
                        print(f"  名称: {task_dict.get('name')}")
                        print(f"  平台: {task_dict.get('platform')}")
                        print(f"  类型: {task_dict.get('task_type')}")
                        print(f"  状态: {task_dict.get('status')}")
                    except Exception as e:
                        print(f"  转换to_dict失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("3. 测试API路由注册")
        print("-" * 60)
        
        with app.app_context():
            from flask import url_for
            try:
                # 检查路由是否注册
                rules = []
                for rule in app.url_map.iter_rules():
                    if 'crawler/tasks' in rule.rule:
                        rules.append(rule.rule)
                
                if rules:
                    print(f"找到相关路由:")
                    for rule in rules:
                        print(f"  {rule}")
                else:
                    print("未找到相关路由！")
            except Exception as e:
                print(f"检查路由失败: {str(e)}")
        
    except Exception as e:
        print(f"\n测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n测试完成！")

