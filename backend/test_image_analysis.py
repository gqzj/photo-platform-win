# -*- coding: utf-8 -*-
"""
图片检测功能测试脚本
用于测试人脸检测、文字检测、模糊检测等功能
"""
import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.image_analysis_service import ImageAnalysisService
from app.utils.config_manager import get_local_image_dir

def test_image_analysis(image_path):
    """测试单张图片的分析功能"""
    print("=" * 80)
    print(f"测试图片: {image_path}")
    print("=" * 80)
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"[错误] 图片文件不存在: {image_path}")
        return
    
    # 获取文件信息
    file_size = os.path.getsize(image_path)
    print(f"文件大小: {file_size / 1024:.2f} KB")
    print()
    
    # 初始化服务
    service = ImageAnalysisService()
    
    # 测试人脸检测
    print("1. 人脸检测测试")
    print("-" * 80)
    try:
        face_count, face_locations = service.detect_faces(image_path)
        print(f"检测到人脸数量: {face_count}")
        if face_locations:
            print(f"人脸位置: {face_locations}")
            for idx, (x, y, w, h) in enumerate(face_locations):
                print(f"  人脸 {idx + 1}: x={x}, y={y}, width={w}, height={h}")
        else:
            print("未检测到人脸")
        print()
    except Exception as e:
        print(f"[错误] 人脸检测失败: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # 测试文字检测
    print("2. 文字检测测试")
    print("-" * 80)
    try:
        has_text = service.detect_text(image_path)
        print(f"是否包含文字: {has_text}")
        print()
    except Exception as e:
        print(f"[错误] 文字检测失败: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # 测试模糊检测
    print("3. 模糊检测测试")
    print("-" * 80)
    try:
        is_blur, blur_value = service.detect_blur(image_path)
        print(f"是否模糊: {is_blur}")
        print(f"模糊度值: {blur_value:.2f}")
        print(f"阈值: 100.0 (低于此值认为模糊)")
        print()
    except Exception as e:
        print(f"[错误] 模糊检测失败: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # 测试完整分析
    print("4. 完整分析测试")
    print("-" * 80)
    try:
        filter_features = ['no_face', 'multiple_faces', 'contains_text', 'blurry']
        result = service.analyze_image(image_path, filter_features)
        
        print("分析结果:")
        # 转换numpy类型为Python原生类型以便JSON序列化
        def convert_to_native(obj):
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, tuple):
                return list(obj)
            else:
                return obj
        
        result_serializable = convert_to_native(result)
        print(json.dumps(result_serializable, ensure_ascii=False, indent=2))
        print()
        
        print("匹配的特征:")
        matched = result.get('matched_features', [])
        if matched:
            for feature in matched:
                print(f"  - {feature}")
        else:
            print("  无匹配特征")
        print()
        
        print("详细信息:")
        details = result.get('details', {})
        for key, value in details.items():
            if key == 'face_locations':
                print(f"  {key}: {len(value) if isinstance(value, list) else 0} 个位置")
            else:
                print(f"  {key}: {value}")
        print()
        
    except Exception as e:
        print(f"[错误] 完整分析失败: {e}")
        import traceback
        traceback.print_exc()
        print()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='图片检测功能测试')
    parser.add_argument('image_path', nargs='?', help='图片路径（相对路径或绝对路径）')
    parser.add_argument('--list', action='store_true', help='列出存储目录中的图片')
    parser.add_argument('--count', type=int, default=5, help='列出图片的数量（默认5张）')
    
    args = parser.parse_args()
    
    if args.list:
        # 列出存储目录中的图片
        storage_dir = get_local_image_dir()
        print(f"图片存储目录: {storage_dir}")
        print()
        
        image_files = []
        for root, dirs, files in os.walk(storage_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                    image_files.append(os.path.join(root, file))
        
        print(f"找到 {len(image_files)} 张图片")
        print()
        
        if image_files:
            print(f"前 {min(args.count, len(image_files))} 张图片:")
            for idx, img_path in enumerate(image_files[:args.count]):
                relative_path = os.path.relpath(img_path, storage_dir)
                print(f"  {idx + 1}. {relative_path}")
            print()
            
            if len(image_files) > 0:
                print("使用示例:")
                print(f"  python test_image_analysis.py \"{os.path.relpath(image_files[0], os.getcwd())}\"")
        else:
            print("未找到图片文件")
        
        return
    
    if not args.image_path:
        print("请提供图片路径，或使用 --list 查看可用图片")
        print()
        print("使用示例:")
        print("  python test_image_analysis.py image.jpg")
        print("  python test_image_analysis.py --list")
        print("  python test_image_analysis.py --list --count 10")
        return
    
    # 处理图片路径
    image_path = args.image_path
    
    # 如果是绝对路径，直接使用
    if os.path.isabs(image_path):
        if not os.path.exists(image_path):
            print(f"[错误] 图片文件不存在: {image_path}")
            return
        image_path = os.path.abspath(image_path)
    else:
        # 如果是相对路径，尝试从存储目录查找
        storage_dir = get_local_image_dir()
        # 先尝试直接路径
        if os.path.exists(image_path):
            image_path = os.path.abspath(image_path)
        # 再尝试从存储目录查找
        elif os.path.exists(os.path.join(storage_dir, image_path)):
            image_path = os.path.join(storage_dir, image_path)
        else:
            print(f"[错误] 找不到图片文件: {args.image_path}")
            print(f"存储目录: {storage_dir}")
            return
    
    # 转换为绝对路径并规范化
    image_path = os.path.abspath(image_path)
    image_path = os.path.normpath(image_path)
    
    # 执行测试
    test_image_analysis(image_path)

if __name__ == '__main__':
    main()

