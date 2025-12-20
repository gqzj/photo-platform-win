# -*- coding: utf-8 -*-
"""测试抓取任务API"""
import requests
import json

print("=" * 60)
print("Test Crawl Task API")
print("=" * 60)

task_id = 5
url = f"http://localhost:8000/api/crawler/tasks/{task_id}/crawl"

print(f"\n1. Testing POST {url}")
print("-" * 60)

try:
    response = requests.post(url, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"SUCCESS")
        print(f"Code: {data.get('code')}")
        print(f"Message: {data.get('message')}")
        if 'data' in data and 'stats' in data.get('data', {}):
            stats = data['data']['stats']
            print(f"\nStats:")
            print(f"  Posts: {stats.get('posts', 0)}")
            print(f"  Comments: {stats.get('comments', 0)}")
            print(f"  Media: {stats.get('media', 0)}")
            print(f"  Images: {stats.get('images', 0)}")
    else:
        print(f"FAILED - Status: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"Response: {response.text[:500]}")
            
except requests.exceptions.Timeout:
    print("ERROR - Request timeout (this is normal for crawl tasks)")
except requests.exceptions.ConnectionError:
    print("ERROR - Cannot connect to backend service!")
except Exception as e:
    print(f"ERROR - {str(e)}")

print("\nTest completed!")

