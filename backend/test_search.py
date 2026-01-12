# -*- coding: utf-8 -*-
"""
测试语义搜索功能
"""
import requests
import json

def test_search():
    """测试搜索功能"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试语义搜索功能")
    print("=" * 60)
    
    # 1. 检查当前编码状态
    print("\n[1] 检查编码状态...")
    try:
        response = requests.get(f"{base_url}/api/semantic-search/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                stats = data['data']
                encoded_count = stats.get('encoded_count', 0)
                print(f"   已编码图片数: {encoded_count}")
                if encoded_count == 0:
                    print("   [WARN] 没有已编码的图片，无法测试搜索功能")
                    return False
    except Exception as e:
        print(f"   [ERROR] 获取统计失败: {str(e)}")
        return False
    
    # 2. 测试文本搜索
    print("\n[2] 测试文本搜索...")
    test_queries = [
        "一只可爱的小猫",
        "美丽的风景",
        "人物肖像",
        "美食"
    ]
    
    for query in test_queries:
        try:
            payload = {"query": query, "top_k": 5}
            response = requests.post(f"{base_url}/api/semantic-search/search/text", 
                                   json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    results = data['data'].get('results', [])
                    total = data['data'].get('total', 0)
                    print(f"   查询: \"{query}\"")
                    print(f"   结果数: {total}")
                    if results:
                        print(f"   前3个结果:")
                        for i, result in enumerate(results[:3], 1):
                            score = result.get('score', 0)
                            image_id = result.get('image_id', 'N/A')
                            print(f"     {i}. image_id={image_id}, score={score:.4f}")
                    print()
        except Exception as e:
            print(f"   [ERROR] 搜索失败: {str(e)}")
    
    print("=" * 60)
    print("[OK] 搜索功能测试完成！")
    print("=" * 60)
    return True

if __name__ == '__main__':
    test_search()
