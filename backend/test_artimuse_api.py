# -*- coding: utf-8 -*-
"""
测试ArtiMuse美学评分接口
"""
import requests
import os
import sys
from pathlib import Path

def test_artimuse_api(image_path=None):
    """测试ArtiMuse接口"""
    
    # 如果没有提供图片路径，尝试找一个测试图片
    if not image_path:
        # 尝试从数据库中找到一张图片
        try:
            from app import create_app
            from app.models.image import Image
            from app.database import db
            
            app = create_app()
            with app.app_context():
                # 查找一张有存储路径的图片
                image = Image.query.filter(Image.storage_path.isnot(None)).first()
                if image and image.storage_path:
                    from app.utils.config_manager import get_local_image_dir
                    storage_base = get_local_image_dir()
                    relative_path = image.storage_path.replace('\\', '/')
                    relative_path = relative_path.lstrip('./').lstrip('.\\')
                    file_path = os.path.join(storage_base, relative_path)
                    file_path = os.path.normpath(file_path)
                    
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        image_path = file_path
                        print(f"使用数据库中的图片: {image_path}")
                    else:
                        print(f"数据库中的图片路径不存在: {file_path}")
                else:
                    print("数据库中没有找到图片")
        except Exception as e:
            print(f"从数据库获取图片失败: {e}")
    
    # 如果还是没有图片路径，提示用户
    if not image_path or not os.path.exists(image_path):
        print("=" * 60)
        print("ArtiMuse接口测试")
        print("=" * 60)
        print("\n使用方法:")
        print("  python test_artimuse_api.py [图片路径]")
        print("\n示例:")
        print("  python test_artimuse_api.py ./test_image.jpg")
        print("\n如果没有提供图片路径，将尝试从数据库中找到一张图片进行测试")
        print("=" * 60)
        
        if not image_path:
            return
    
    # 测试接口
    api_url = 'http://localhost:5001/api/evaluate'
    
    print(f"\n测试接口: {api_url}")
    print(f"图片路径: {image_path}")
    print(f"图片大小: {os.path.getsize(image_path) / 1024:.2f} KB")
    print("-" * 60)
    
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"错误: 图片文件不存在: {image_path}")
            return
        
        # 发送请求
        print("正在发送请求...")
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(
                api_url,
                files=files,
                timeout=30
            )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result_data = response.json()
                print("\n响应数据:")
                print("-" * 60)
                import json
                print(json.dumps(result_data, indent=2, ensure_ascii=False))
                print("-" * 60)
                
                # 检查评分字段
                score = result_data.get('score') or result_data.get('aesthetic_score')
                if score is not None:
                    print(f"\n[OK] 成功获取评分: {score}")
                else:
                    print("\n[WARNING] 警告: 响应中没有找到 'score' 或 'aesthetic_score' 字段")
                    print("响应中的字段:", list(result_data.keys()))
            except Exception as e:
                print(f"\n[X] 解析JSON响应失败: {e}")
                print(f"原始响应内容: {response.text[:500]}")
        else:
            print(f"\n[X] 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("\n[X] 连接失败: 无法连接到 http://localhost:5001")
        print("请确保ArtiMuse服务正在运行")
    except requests.exceptions.Timeout:
        print("\n[X] 请求超时: 接口响应时间超过30秒")
    except Exception as e:
        print(f"\n[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 获取命令行参数
    image_path = None
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    
    test_artimuse_api(image_path)

