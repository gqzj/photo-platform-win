# -*- coding: utf-8 -*-
"""
一键还原所有回收站图片到images表的工具脚本
使用方法: python restore_all_recycled_images.py
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.image_recycle import ImageRecycle
from app.models.image import Image
from sqlalchemy import text

def restore_all_recycled_images():
    """一键还原所有回收站图片到images表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取所有回收站图片
            recycle_images = ImageRecycle.query.all()
            total_count = len(recycle_images)
            
            if total_count == 0:
                print("回收站中没有图片需要还原")
                return
            
            print("=" * 80)
            print(f"开始还原回收站图片，共 {total_count} 张")
            print("=" * 80)
            
            restored_count = 0
            failed_count = 0
            errors = []
            
            for idx, recycle_image in enumerate(recycle_images, 1):
                try:
                    print(f"[{idx}/{total_count}] 处理图片: ID={recycle_image.id}, filename={recycle_image.filename}")
                    
                    # 准备图片数据
                    image_data = {
                        'filename': recycle_image.filename,
                        'storage_path': recycle_image.storage_path,
                        'original_url': recycle_image.original_url,
                        'status': 'active',
                        'created_at': recycle_image.created_at,
                        'storage_mode': recycle_image.storage_mode,
                        'source_site': recycle_image.source_site,
                        'keyword': recycle_image.keyword,
                        'hash_tags_json': recycle_image.hash_tags_json,
                        'visit_url': recycle_image.visit_url,
                        'image_hash': recycle_image.image_hash,
                        'width': recycle_image.width,
                        'height': recycle_image.height,
                        'format': recycle_image.format
                    }
                    
                    # 如果original_image_id存在，尝试使用该id
                    if recycle_image.original_image_id:
                        # 检查images表中是否已存在该id
                        existing_image = Image.query.get(recycle_image.original_image_id)
                        if existing_image:
                            # 如果存在，更新记录
                            for key, value in image_data.items():
                                setattr(existing_image, key, value)
                            restored_image = existing_image
                            print(f"  ✓ 更新已存在的图片记录: id={recycle_image.original_image_id}")
                        else:
                            # 如果不存在，创建新记录并指定id
                            try:
                                db.session.execute(
                                    text("""
                                        INSERT INTO images (id, filename, storage_path, original_url, status, created_at, 
                                                            storage_mode, source_site, keyword, hash_tags_json, visit_url, 
                                                            image_hash, width, height, format)
                                        VALUES (:id, :filename, :storage_path, :original_url, :status, :created_at,
                                                :storage_mode, :source_site, :keyword, :hash_tags_json, :visit_url,
                                                :image_hash, :width, :height, :format)
                                    """),
                                    {
                                        'id': recycle_image.original_image_id,
                                        'filename': image_data['filename'],
                                        'storage_path': image_data['storage_path'],
                                        'original_url': image_data['original_url'],
                                        'status': image_data['status'],
                                        'created_at': image_data['created_at'],
                                        'storage_mode': image_data['storage_mode'],
                                        'source_site': image_data['source_site'],
                                        'keyword': image_data['keyword'],
                                        'hash_tags_json': image_data['hash_tags_json'],
                                        'visit_url': image_data['visit_url'],
                                        'image_hash': image_data['image_hash'],
                                        'width': image_data['width'],
                                        'height': image_data['height'],
                                        'format': image_data['format']
                                    }
                                )
                                db.session.commit()
                                restored_image = Image.query.get(recycle_image.original_image_id)
                                print(f"  ✓ 创建新图片记录并指定id: id={recycle_image.original_image_id}")
                            except Exception as e:
                                db.session.rollback()
                                # 如果插入失败，创建新记录让数据库自动分配id
                                print(f"  ⚠ 无法使用original_image_id {recycle_image.original_image_id}，创建新记录: {e}")
                                restored_image = Image(**image_data)
                                db.session.add(restored_image)
                                db.session.commit()
                                db.session.refresh(restored_image)
                                print(f"  ✓ 创建新图片记录（自动分配id）: id={restored_image.id}")
                    else:
                        # 如果没有original_image_id，创建新记录
                        restored_image = Image(**image_data)
                        db.session.add(restored_image)
                        db.session.commit()
                        db.session.refresh(restored_image)
                        print(f"  ✓ 创建新图片记录（自动分配id）: id={restored_image.id}")
                    
                    # 从回收站删除
                    db.session.delete(recycle_image)
                    db.session.commit()
                    
                    restored_count += 1
                    print(f"  ✓ 图片已还原: recycle_id={recycle_image.id}, image_id={restored_image.id}")
                    
                except Exception as e:
                    db.session.rollback()
                    error_msg = f"还原图片失败 (recycle_id={recycle_image.id}): {str(e)}"
                    errors.append(error_msg)
                    print(f"  ✗ {error_msg}")
                    failed_count += 1
                    continue
            
            # 输出统计信息
            print("=" * 80)
            print("还原完成！")
            print("=" * 80)
            print(f"总计: {total_count} 张")
            print(f"成功: {restored_count} 张")
            print(f"失败: {failed_count} 张")
            
            if errors:
                print("\n错误详情:")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")
            
            print("=" * 80)
            
        except Exception as e:
            db.session.rollback()
            print(f"执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    # 确保控制台输出使用UTF-8
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    print("=" * 80)
    print("一键还原所有回收站图片工具")
    print("=" * 80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 确认操作
    confirm = input("确定要还原所有回收站的图片吗？(yes/no): ")
    if confirm.lower() not in ['yes', 'y', '是']:
        print("操作已取消")
        sys.exit(0)
    
    print()
    success = restore_all_recycled_images()
    
    if success:
        print("\n工具执行完成！")
    else:
        print("\n工具执行失败！")
        sys.exit(1)

