# -*- coding: utf-8 -*-
"""
测试手工风格API
"""
import requests

def test_api():
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试手工风格API")
    print("=" * 60)
    
    # 测试获取列表
    print("\n[1] 测试获取手工风格列表...")
    try:
        response = requests.get(f"{base_url}/api/manual-styles", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] API测试成功")
            print(f"   响应代码: {data.get('code')}")
            print(f"   消息: {data.get('message')}")
            if 'data' in data:
                print(f"   风格数量: {len(data['data'].get('list', []))}")
        else:
            print(f"[ERROR] API返回错误: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] API测试失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_api()
