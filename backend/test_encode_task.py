# -*- coding: utf-8 -*-
"""
测试图片编码任务
"""
import requests
import time
import json

def test_encode_task():
    """测试编码任务"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试图片编码任务")
    print("=" * 60)
    
    # 1. 启动编码任务
    print("\n[1] 启动编码任务...")
    try:
        response = requests.post(f"{base_url}/api/semantic-search/encode/start", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 编码任务启动成功")
            print(f"   响应代码: {data.get('code')}")
            print(f"   消息: {data.get('message')}")
        else:
            print(f"[ERROR] 启动失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[ERROR] 启动编码任务失败: {str(e)}")
        return False
    
    # 2. 监控编码进度
    print("\n[2] 监控编码进度（每5秒检查一次，最多检查10次）...")
    for i in range(10):
        time.sleep(5)
        try:
            response = requests.get(f"{base_url}/api/semantic-search/encode/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    status = data['data']
                    running = status.get('running', False)
                    total = status.get('total', 0)
                    processed = status.get('processed', 0)
                    success = status.get('success', 0)
                    failed = status.get('failed', 0)
                    
                    if total > 0:
                        progress = (processed / total * 100) if total > 0 else 0
                        print(f"   进度: {processed}/{total} ({progress:.1f}%) - 成功: {success}, 失败: {failed}")
                    
                    if not running:
                        print(f"\n[OK] 编码任务完成！")
                        print(f"   总计: {total}")
                        print(f"   成功: {success}")
                        print(f"   失败: {failed}")
                        break
        except Exception as e:
            print(f"   [WARN] 获取状态失败: {str(e)}")
    
    # 3. 检查最终统计
    print("\n[3] 检查最终统计...")
    try:
        response = requests.get(f"{base_url}/api/semantic-search/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                stats = data['data']
                print(f"   总图片数: {stats.get('total_images', 0)}")
                print(f"   已编码数: {stats.get('encoded_count', 0)}")
                print(f"   FAISS向量数: {stats.get('collection_stats', {}).get('total_vectors', 0)}")
    except Exception as e:
        print(f"   [WARN] 获取统计失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("[OK] 编码任务测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    test_encode_task()
