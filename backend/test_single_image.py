# -*- coding: utf-8 -*-
"""直接测试单张图片"""
import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 确保UTF-8编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from app.services.image_analysis_service import ImageAnalysisService

# 直接使用文件路径
image_path = r'F:\ai_platform\download_images\拍出氛围感\image_6878ecfd000000001202111f_0.jpg'

print("=" * 80)
print(f"测试图片: {image_path}")
print("=" * 80)

# 检查文件是否存在
if not os.path.exists(image_path):
    print(f"[错误] 图片文件不存在: {image_path}")
    sys.exit(1)

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

