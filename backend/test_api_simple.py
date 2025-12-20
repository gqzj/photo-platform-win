# -*- coding: utf-8 -*-
"""简单API测试"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.crawler_task import CrawlerTask

app = create_app()

print("=" * 60)
print("API Test")
print("=" * 60)

# Test database query
print("\n1. Test database query")
print("-" * 60)

try:
    with app.app_context():
        total = CrawlerTask.query.count()
        print(f"Total tasks: {total}")
        
        if total > 0:
            tasks = CrawlerTask.query.limit(3).all()
            print(f"Found {len(tasks)} tasks")
            
            for i, task in enumerate(tasks, 1):
                try:
                    task_dict = task.to_dict()
                    print(f"Task {i} to_dict() OK, fields: {len(task_dict)}")
                except Exception as e:
                    print(f"Task {i} to_dict() FAILED: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
except Exception as e:
    print(f"Database query FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

# Test API endpoint
print("\n2. Test API endpoint")
print("-" * 60)

try:
    with app.test_client() as client:
        response = client.get('/api/crawler/tasks?page=1&page_size=10')
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("API request SUCCESS")
            data = response.get_json()
            print(f"Response code: {data.get('code')}")
            print(f"Response message: {data.get('message')}")
            if 'data' in data:
                print(f"Total: {data['data'].get('total')}")
                print(f"List length: {len(data['data'].get('list', []))}")
        else:
            print(f"API request FAILED, status: {response.status_code}")
            try:
                error_data = response.get_json()
                print(f"Error response: {error_data}")
            except:
                error_text = response.get_data(as_text=True)
                print(f"Error text: {error_text[:500]}")
                
except Exception as e:
    print(f"API test FAILED: {str(e)}")
    import traceback
    traceback.print_exc()

print("\nTest completed!")

