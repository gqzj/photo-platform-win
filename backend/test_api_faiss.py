# -*- coding: utf-8 -*-
"""
测试FAISS语义搜索API
"""
import requests
import json

def test_api():
    """测试API接口"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试FAISS语义搜索API")
    print("=" * 60)
    
    # 1. 测试统计接口
    print("\n[1] 测试统计接口...")
    try:
        response = requests.get(f"{base_url}/api/semantic-search/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 统计接口测试成功")
            print(f"   响应代码: {data.get('code')}")
            print(f"   消息: {data.get('message')}")
            if 'data' in data:
                stats = data['data']
                print(f"   总图片数: {stats.get('total_images', 0)}")
                print(f"   已编码数: {stats.get('encoded_count', 0)}")
                print(f"   未编码数: {stats.get('not_encoded_count', 0)}")
                if 'collection_stats' in stats:
                    cs = stats['collection_stats']
                    print(f"   FAISS索引类型: {cs.get('index_type', 'N/A')}")
                    print(f"   FAISS向量数: {cs.get('total_vectors', 0)}")
                    print(f"   向量维度: {cs.get('dimension', 0)}")
                    if 'error' in cs:
                        print(f"   [WARN] 错误: {cs['error']}")
        else:
            print(f"[ERROR] 统计接口返回错误: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] 统计接口测试失败: {str(e)}")
        return False
    
    # 2. 测试文本搜索接口（即使索引为空也测试）
    print("\n[2] 测试文本搜索接口...")
    try:
        payload = {"query": "一只可爱的小猫", "top_k": 5}
        response = requests.post(f"{base_url}/api/semantic-search/search/text", 
                               json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 文本搜索接口测试成功")
            print(f"   响应代码: {data.get('code')}")
            print(f"   查询文本: {data.get('data', {}).get('query', 'N/A')}")
            print(f"   结果数量: {data.get('data', {}).get('total', 0)}")
        else:
            print(f"[WARN] 文本搜索接口返回: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
    except Exception as e:
        print(f"[WARN] 文本搜索接口测试: {str(e)}")
    
    # 3. 测试编码状态接口
    print("\n[3] 测试编码状态接口...")
    try:
        response = requests.get(f"{base_url}/api/semantic-search/encode/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 编码状态接口测试成功")
            if 'data' in data:
                status = data['data']
                print(f"   任务运行中: {status.get('running', False)}")
                print(f"   总数: {status.get('total', 0)}")
                print(f"   已处理: {status.get('processed', 0)}")
                print(f"   成功: {status.get('success', 0)}")
                print(f"   失败: {status.get('failed', 0)}")
        else:
            print(f"[WARN] 编码状态接口返回: {response.status_code}")
    except Exception as e:
        print(f"[WARN] 编码状态接口测试: {str(e)}")
    
    print("\n" + "=" * 60)
    print("[OK] API测试完成！")
    print("=" * 60)
    return True

if __name__ == '__main__':
    test_api()
