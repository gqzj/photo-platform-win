"""模拟前端请求测试API"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("模拟前端请求测试")
print("=" * 60)

# 测试直接访问后端
print("\n1. 直接访问后端 (http://localhost:8000/api/crawler/tasks)")
print("-" * 60)

try:
    response = requests.get(
        'http://localhost:8000/api/crawler/tasks',
        params={'page': 1, 'page_size': 10},
        timeout=5
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应: code={data.get('code')}, total={data.get('data', {}).get('total')}")
    else:
        print(f"错误响应: {response.text[:200]}")
except requests.exceptions.ConnectionError:
    print("无法连接到后端服务！请确保后端服务正在运行在 http://localhost:8000")
except Exception as e:
    print(f"请求失败: {str(e)}")

# 测试通过代理访问（模拟前端）
print("\n2. 通过代理访问 (http://localhost:3000/api/crawler/tasks)")
print("-" * 60)

try:
    response = requests.get(
        'http://localhost:3000/api/crawler/tasks',
        params={'page': 1, 'page_size': 10},
        timeout=5
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应: code={data.get('code')}, total={data.get('data', {}).get('total')}")
    else:
        print(f"错误响应: {response.text[:200]}")
except requests.exceptions.ConnectionError:
    print("无法连接到前端代理！请确保前端服务正在运行在 http://localhost:3000")
except Exception as e:
    print(f"请求失败: {str(e)}")

print("\n测试完成！")

