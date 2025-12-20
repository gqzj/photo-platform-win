# -*- coding: utf-8 -*-
"""检查后端服务状态"""
import requests
import sys

print("=" * 60)
print("Backend Service Check")
print("=" * 60)

# Check if backend is running
print("\n1. Check backend service (http://localhost:8000)")
print("-" * 60)

try:
    response = requests.get('http://localhost:8000/api/crawler/tasks', 
                          params={'page': 1, 'page_size': 10}, 
                          timeout=3)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"SUCCESS - Code: {data.get('code')}, Total: {data.get('data', {}).get('total')}")
    else:
        print(f"FAILED - Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except requests.exceptions.ConnectionError:
    print("ERROR - Cannot connect to backend service!")
    print("Please make sure backend is running on port 8000")
except Exception as e:
    print(f"ERROR - {str(e)}")

# Check proxy
print("\n2. Check proxy (http://localhost:3000/api/crawler/tasks)")
print("-" * 60)

try:
    response = requests.get('http://localhost:3000/api/crawler/tasks',
                          params={'page': 1, 'page_size': 10},
                          timeout=3)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"SUCCESS - Code: {data.get('code')}, Total: {data.get('data', {}).get('total')}")
    else:
        print(f"FAILED - Status: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error response: {error_data}")
        except:
            print(f"Response text: {response.text[:500]}")
except requests.exceptions.ConnectionError:
    print("ERROR - Cannot connect to frontend proxy!")
    print("Please make sure frontend is running on port 3000")
except Exception as e:
    print(f"ERROR - {str(e)}")

print("\nCheck completed!")

