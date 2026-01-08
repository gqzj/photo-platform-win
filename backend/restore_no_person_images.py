# -*- coding: utf-8 -*-
"""
恢复回收站中清洗原因为"无人物"的图片（多线程版本）
使用方法: python restore_no_person_images.py
"""
import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.image_recycle import ImageRecycle
from app.models.image import Image
from sqlalchemy import text, or_

# 线程安全的计数器
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
            return self._value
    
    @property
    def value(self):
        with self._lock:
            return self._value

def restore_single_image(recycle_image_id, app_instance, total_count, counter, restored_counter, failed_counter, errors_list, lock):
    """
    恢复单张图片（线程函数）
    
    Args:
        recycle_image_id: 回收站图片ID
        app_instance: Flask应用实例（共享）
        total_count: 总数量（用于显示进度）
        counter: 已处理计数器
        restored_counter: 成功恢复计数器
        failed_counter: 失败计数器
        errors_list: 错误列表
        lock: 线程锁（用于保护共享资源）
    """
    # 使用共享的app实例，但每个线程需要自己的app context和数据库会话
    with app_instance.app_context():
        try:
            # 重新查询图片（避免跨线程对象共享问题）
            # 使用with_for_update锁定记录，防止并发冲突
            try:
                recycle_image = ImageRecycle.query.filter_by(id=recycle_image_id).first()
                if not recycle_image:
                    # 记录可能已被其他线程处理，不算失败
                    current = counter.increment()
                    return True
            except Exception as query_error:
                # 查询异常，可能是记录已被删除
                current = counter.increment()
                return True
            
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
                    except Exception as e:
                        db.session.rollback()
                        # 如果插入失败，创建新记录让数据库自动分配id
                        restored_image = Image(**image_data)
                        db.session.add(restored_image)
                        db.session.commit()
                        db.session.refresh(restored_image)
            else:
                # 如果没有original_image_id，创建新记录
                restored_image = Image(**image_data)
                db.session.add(restored_image)
                db.session.commit()
                db.session.refresh(restored_image)
            
            # 从回收站删除（使用with_for_update确保线程安全）
            try:
                # 再次检查记录是否存在（防止其他线程已删除）
                recycle_image_check = ImageRecycle.query.get(recycle_image_id)
                if not recycle_image_check:
                    # 记录已被其他线程删除，不算失败，直接返回
                    current = counter.increment()
                    return True
                
                db.session.delete(recycle_image_check)
                db.session.commit()
            except Exception as delete_error:
                db.session.rollback()
                # 如果删除失败，可能是记录已被删除，不算失败
                current = counter.increment()
                return True
            
            # 更新计数器
            current = counter.increment()
            restored_counter.increment()
            
            # 每100张打印一次进度
            if current % 100 == 0 or current == total_count:
                with lock:
                    print(f"[进度: {current}/{total_count}] 已恢复: {restored_counter.value}, 失败: {failed_counter.value}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"还原图片失败 (recycle_id={recycle_image_id}): {str(e)}"
            # 检查是否是记录不存在的错误（可能是并发导致）
            if "不存在" in str(e) or "not found" in str(e).lower():
                # 记录可能已被其他线程处理，不算失败
                current = counter.increment()
                return True
            
            # 其他错误才记录为失败
            with lock:
                failed_counter.increment()
                errors_list.append(error_msg)
                if len(errors_list) <= 20:  # 增加错误记录数量
                    print(f"  ✗ {error_msg}")
            return False

def restore_no_person_images(max_workers=5):
    """恢复回收站中清洗原因为"无人物"的图片（多线程版本）"""
    app = create_app()
    
    with app.app_context():
        try:
            # 查找清洗原因为"无人物"的回收站图片
            recycle_images = ImageRecycle.query.filter(
                or_(
                    ImageRecycle.cleaning_reason.like('%no_person%'),
                    ImageRecycle.cleaning_reason.like('%无人物%')
                )
            ).all()
            
            total_count = len(recycle_images)
            
            if total_count == 0:
                print("回收站中没有清洗原因为'无人物'的图片需要还原")
                return True
            
            print("=" * 80)
            print(f"开始还原清洗原因为'无人物'的回收站图片，共 {total_count} 张")
            print(f"使用 {max_workers} 个线程并行处理（共享app实例以节省文件句柄）")
            print("=" * 80)
            
            if total_count > 0:
                print(f"清洗原因示例（前5条）:")
                for img in recycle_images[:5]:
                    print(f"  - {img.cleaning_reason}")
                if total_count > 5:
                    print(f"  ... 还有 {total_count - 5} 条")
                print()
            
            # 线程安全的计数器和列表
            counter = ThreadSafeCounter()
            restored_counter = ThreadSafeCounter()
            failed_counter = ThreadSafeCounter()
            errors_list = []
            lock = threading.Lock()
            
            # 获取所有图片ID
            recycle_image_ids = [img.id for img in recycle_images]
            
            # 使用线程池并行处理
            # 创建共享的app实例，避免每个线程都创建新的app（导致文件句柄耗尽）
            shared_app = create_app()
            start_time = datetime.now()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                futures = {
                    executor.submit(
                        restore_single_image,
                        img_id,
                        shared_app,
                        total_count,
                        counter,
                        restored_counter,
                        failed_counter,
                        errors_list,
                        lock
                    ): img_id for img_id in recycle_image_ids
                }
                
                # 等待所有任务完成
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    try:
                        future.result()
                    except Exception as e:
                        with lock:
                            failed_counter.increment()
                            errors_list.append(f"任务执行异常: {str(e)}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 输出统计信息
            print("=" * 80)
            print("还原完成！")
            print("=" * 80)
            print(f"总计: {total_count} 张")
            print(f"成功: {restored_counter.value} 张")
            print(f"失败: {failed_counter.value} 张")
            print(f"耗时: {duration:.2f} 秒")
            print(f"平均速度: {total_count / duration:.2f} 张/秒")
            
            if errors_list:
                print(f"\n错误详情（显示前10条）:")
                for i, error in enumerate(errors_list[:10], 1):
                    print(f"  {i}. {error}")
                if len(errors_list) > 10:
                    print(f"  ... 还有 {len(errors_list) - 10} 个错误")
            
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
    print("恢复清洗原因为'无人物'的回收站图片工具（多线程版本）")
    print("=" * 80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 先查询一下有多少张图片
    app = create_app()
    with app.app_context():
        count = ImageRecycle.query.filter(
            or_(
                ImageRecycle.cleaning_reason.like('%no_person%'),
                ImageRecycle.cleaning_reason.like('%无人物%')
            )
        ).count()
        print(f"找到 {count} 张清洗原因为'无人物'的图片")
        print()
    
    if count == 0:
        print("没有找到需要恢复的图片，退出")
        sys.exit(0)
    
    # 获取线程数（可通过环境变量设置，默认5，避免文件句柄耗尽）
    max_workers = int(os.environ.get('MAX_WORKERS', '5'))
    print(f"将使用 {max_workers} 个线程并行处理（建议不超过5个，避免文件句柄耗尽）")
    print()
    
    # 确认操作（支持非交互式运行，通过环境变量或命令行参数）
    auto_confirm = os.environ.get('AUTO_CONFIRM', '').lower() in ['yes', 'y', 'true', '1']
    if not auto_confirm:
        try:
            confirm = input("确定要恢复这些图片吗？(yes/no): ")
            if confirm.lower() not in ['yes', 'y', '是']:
                print("操作已取消")
                sys.exit(0)
        except EOFError:
            # 非交互式环境，默认执行
            print("非交互式环境，自动确认执行")
    
    print()
    success = restore_no_person_images(max_workers=max_workers)
    
    if success:
        print("\n工具执行完成！")
    else:
        print("\n工具执行失败！")
        sys.exit(1)
