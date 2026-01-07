# -*- coding: utf-8 -*-
"""
批量生成所有LUT文件的缩略图
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models.lut_file import LutFile
from app.utils.config_manager import get_local_image_dir
from app.services.lut_application_service import LutApplicationService
import traceback

def get_lut_storage_dir():
    """获取Lut文件存储目录"""
    base_dir = get_local_image_dir()
    lut_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'luts')
    return lut_dir

def get_lut_thumbnail_dir():
    """获取LUT缩略图存储目录"""
    base_dir = get_local_image_dir()
    thumbnail_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'lut_thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)
    return thumbnail_dir

def generate_lut_thumbnail(lut_file_id, lut_file_path):
    """
    生成LUT文件的缩略图（应用LUT到lut_standard.png）
    
    Args:
        lut_file_id: LUT文件ID
        lut_file_path: LUT文件路径
    
    Returns:
        缩略图路径（相对于存储目录）或None
    """
    try:
        # 查找lut_standard.png文件（在backend目录下）
        # __file__ 是 backend/generate_all_lut_thumbnails.py
        # 直接使用当前文件的目录作为backend_dir
        current_file = os.path.abspath(__file__)
        backend_dir = os.path.dirname(current_file)
        
        standard_image_path = os.path.join(backend_dir, 'lut_standard.png')
        
        if not os.path.exists(standard_image_path):
            # 如果lut_standard.png不存在，尝试standard.png
            standard_image_path = os.path.join(backend_dir, 'standard.png')
            if not os.path.exists(standard_image_path):
                print(f"  警告: 标准图文件不存在: lut_standard.png 或 standard.png")
                return None
        
        # 应用LUT到标准图
        lut_service = LutApplicationService()
        
        # 生成缩略图路径
        thumbnail_dir = get_lut_thumbnail_dir()
        thumbnail_filename = f"thumbnail_{lut_file_id}.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
        
        success, error_msg = lut_service.apply_lut_to_image(
            standard_image_path,
            lut_file_path,
            thumbnail_path
        )
        
        if success:
            # 返回相对路径
            relative_path = f"lut_thumbnails/{thumbnail_filename}"
            print(f"  ✓ 缩略图生成成功: {relative_path}")
            return relative_path
        else:
            print(f"  ✗ 缩略图生成失败: {error_msg}")
            return None
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"  ✗ 生成缩略图异常: {str(e)}")
        return None

def generate_all_thumbnails():
    """为所有LUT文件生成缩略图"""
    app = create_app()
    with app.app_context():
        try:
            # 获取所有.cube格式的LUT文件
            lut_files = LutFile.query.filter(
                db.func.lower(LutFile.original_filename).like('%.cube')
            ).all()
            
            total_count = len(lut_files)
            print(f"找到 {total_count} 个.cube格式的LUT文件")
            
            if total_count == 0:
                print("没有找到.cube格式的LUT文件")
                return
            
            # 统计
            need_generate = 0
            already_have = 0
            success_count = 0
            failed_count = 0
            
            storage_dir = get_lut_storage_dir()
            
            for idx, lut_file in enumerate(lut_files, 1):
                print(f"\n[{idx}/{total_count}] 处理文件: {lut_file.original_filename} (ID: {lut_file.id})")
                
                # 检查是否已有缩略图
                if lut_file.thumbnail_path:
                    print(f"  - 已有缩略图: {lut_file.thumbnail_path}")
                    already_have += 1
                    continue
                
                need_generate += 1
                
                # 检查文件是否存在
                file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
                if not os.path.exists(file_path):
                    print(f"  ✗ 文件不存在: {file_path}")
                    failed_count += 1
                    continue
                
                # 生成缩略图
                thumbnail_path = generate_lut_thumbnail(lut_file.id, file_path)
                
                if thumbnail_path:
                    # 更新数据库
                    lut_file.thumbnail_path = thumbnail_path
                    db.session.commit()
                    success_count += 1
                else:
                    failed_count += 1
            
            # 输出统计信息
            print("\n" + "=" * 60)
            print("生成完成统计:")
            print(f"  总文件数: {total_count}")
            print(f"  已有缩略图: {already_have}")
            print(f"  需要生成: {need_generate}")
            print(f"  成功生成: {success_count}")
            print(f"  生成失败: {failed_count}")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            error_detail = traceback.format_exc()
            print(f"批量生成缩略图失败: {error_detail}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("开始批量生成LUT文件缩略图")
    print("=" * 60)
    generate_all_thumbnails()
    print("\n批量生成完成！")

