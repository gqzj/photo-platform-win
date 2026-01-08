# -*- coding: utf-8 -*-
"""
数据清洗服务
执行清洗任务，分析图片并移动到回收站
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import or_

from app.database import db
from app.models.image import Image
from app.models.image_recycle import ImageRecycle
from app.models.data_cleaning_task import DataCleaningTask
from app.services.image_analysis_service import ImageAnalysisService
from app.utils.config_manager import get_local_image_dir

logger = logging.getLogger(__name__)

class DataCleaningService:
    """数据清洗服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.image_analysis = ImageAnalysisService()
        self.storage_base = get_local_image_dir()
    
    def _get_image_absolute_path(self, image: Image) -> Optional[str]:
        """
        获取图片的绝对路径
        
        Args:
            image: Image对象
            
        Returns:
            str: 绝对路径，如果文件不存在则返回None
        """
        try:
            # 规范化路径
            relative_path = image.storage_path.replace('\\', '/')
            relative_path = relative_path.lstrip('./').lstrip('.\\')
            
            # 拼接完整路径
            file_path = os.path.join(self.storage_base, relative_path)
            file_path = os.path.normpath(file_path)
            
            # 检查文件是否存在
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return file_path
            else:
                logger.warning(f"图片文件不存在: {file_path}, storage_path: {image.storage_path}")
                return None
        except Exception as e:
            logger.error(f"获取图片路径失败: {e}", exc_info=True)
            return None
    
    def _move_to_recycle(self, image: Image, task_id: int, reason: str) -> bool:
        """
        将图片移动到回收站
        
        Args:
            image: Image对象
            task_id: 清洗任务ID
            reason: 清洗原因
            
        Returns:
            bool: 是否成功
        """
        try:
            # 创建回收站记录
            recycle_data = {
                'original_image_id': image.id,
                'filename': image.filename,
                'storage_path': image.storage_path,
                'original_url': image.original_url,
                'status': 'recycled',
                'created_at': image.created_at,
                'storage_mode': image.storage_mode,
                'source_site': image.source_site,
                'keyword': image.keyword,
                'hash_tags_json': image.hash_tags_json,
                'visit_url': image.visit_url,
                'image_hash': image.image_hash,
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'cleaning_task_id': task_id,
                'cleaning_reason': reason,
                'recycled_at': datetime.now()
            }
            
            recycle_obj = ImageRecycle(**recycle_data)
            db.session.add(recycle_obj)
            
            # 从images表删除
            db.session.delete(image)
            
            db.session.commit()
            
            logger.info(f"图片已移动到回收站: image_id={image.id}, reason={reason}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"移动图片到回收站失败: {e}", exc_info=True)
            return False
    
    def _get_filter_keywords(self, task: DataCleaningTask) -> Optional[List[str]]:
        """
        获取任务的筛选关键字列表
        
        Args:
            task: DataCleaningTask对象
            
        Returns:
            Optional[List[str]]: 关键字列表，如果为None表示处理所有关键字（"全部"）
        """
        try:
            if task.filter_keywords:
                keywords = json.loads(task.filter_keywords)
                if isinstance(keywords, list):
                    keywords = [k.strip() for k in keywords if k.strip()]
                    
                    # 检查是否包含"全部"
                    if '全部' in keywords:
                        logger.info(f"关键字包含'全部'，将处理所有关键字的图片")
                        return None  # 返回None表示处理所有关键字
                    else:
                        return keywords
            return []
        except Exception as e:
            logger.error(f"解析筛选关键字失败: {e}", exc_info=True)
            return []
    
    def _get_filter_features(self, task: DataCleaningTask) -> List[str]:
        """
        获取任务的筛选特征列表
        
        Args:
            task: DataCleaningTask对象
            
        Returns:
            List[str]: 特征列表
        """
        try:
            if task.filter_features:
                features = json.loads(task.filter_features)
                if isinstance(features, list):
                    return features
            return []
        except Exception as e:
            logger.error(f"解析筛选特征失败: {e}", exc_info=True)
            return []
    
    def execute_cleaning_task(self, task_id: int) -> Dict:
        """
        执行清洗任务
        
        Args:
            task_id: 清洗任务ID
            
        Returns:
            Dict: 执行结果
        """
        try:
            # 获取任务
            task = DataCleaningTask.query.get(task_id)
            if not task:
                return {
                    'success': False,
                    'message': f'任务不存在: {task_id}'
                }
            
            # 获取筛选条件
            filter_features = self._get_filter_features(task)
            filter_keywords = self._get_filter_keywords(task)
            
            if not filter_features:
                task.status = 'failed'
                task.last_error = '未设置筛选特征'
                task.finished_at = datetime.now()
                db.session.commit()
                return {
                    'success': False,
                    'message': '未设置筛选特征'
                }
            
            logger.info(f"开始执行清洗任务 {task_id}: features={filter_features}, keywords={filter_keywords if filter_keywords is not None else '全部'}")
            
            # 构建查询条件
            query = Image.query.filter(Image.status == 'active')
            
            # 如果设置了关键字筛选，添加关键字条件
            # 如果 filter_keywords 为 None，表示处理所有关键字（"全部"），不添加筛选条件
            if filter_keywords is not None and len(filter_keywords) > 0:
                keyword_conditions = [Image.keyword.like(f'%{kw}%') for kw in filter_keywords]
                query = query.filter(or_(*keyword_conditions))
            
            # 获取所有符合条件的图片
            images = query.all()
            total_count = len(images)
            
            logger.info(f"找到 {total_count} 张符合条件的图片")
            
            # 更新任务状态和总数量
            task.status = 'running'
            task.started_at = datetime.now()
            task.processed_count = 0
            task.total_count = total_count
            task.last_error = None
            db.session.commit()
            
            # 统计信息
            stats = {
                'total': total_count,
                'processed': 0,
                'recycled': 0,
                'skipped': 0,
                'errors': []
            }
            
            # 处理每张图片
            for idx, image in enumerate(images):
                try:
                    # 检查任务状态，如果被重置为pending，停止执行
                    db.session.refresh(task)
                    if task.status != 'running':
                        logger.info(f"任务状态已变为 {task.status}，停止执行: task_id={task_id}")
                        stats['skipped'] += total_count - idx
                        break
                    
                    # 更新处理计数
                    task.processed_count = idx + 1
                    db.session.commit()
                    
                    # 获取图片绝对路径
                    image_path = self._get_image_absolute_path(image)
                    if not image_path:
                        stats['skipped'] += 1
                        logger.warning(f"跳过图片（文件不存在）: image_id={image.id}, storage_path={image.storage_path}")
                        continue
                    
                    # 记录图片路径
                    logger.info(f"[{idx + 1}/{total_count}] 开始分析图片: image_id={image.id}, path={image_path}")
                    
                    # 分析图片
                    analysis_result = self.image_analysis.analyze_image(image_path, filter_features)
                    
                    # 记录完整的分析结果
                    import json
                    logger.info(f"图片分析结果 - image_id={image.id}, path={image_path}")
                    logger.info(f"  完整分析结果: {json.dumps(analysis_result, ensure_ascii=False, indent=2)}")
                    
                    # 记录分析结果详情
                    matched_features = analysis_result.get('matched_features', [])
                    details = analysis_result.get('details', {})
                    
                    logger.info(f"  匹配特征: {matched_features if matched_features else '无'}")
                    if 'face_count' in details:
                        logger.info(f"  人脸数量: {details['face_count']}")
                    if 'has_text' in details:
                        logger.info(f"  包含文字: {details['has_text']}")
                    if 'is_blur' in details:
                        logger.info(f"  是否模糊: {details['is_blur']}, 模糊度值: {details.get('blur_value', 'N/A')}")
                    
                    # 检查是否匹配筛选条件
                    if matched_features:
                        # 匹配到筛选条件，移动到回收站
                        reason = ', '.join(matched_features)
                        logger.info(f"图片匹配筛选条件，准备回收: image_id={image.id}, reason={reason}")
                        if self._move_to_recycle(image, task_id, reason):
                            stats['recycled'] += 1
                            logger.info(f"✓ 图片已回收: image_id={image.id}, path={image_path}, reason={reason}")
                        else:
                            error_msg = f"image_id={image.id}: 移动到回收站失败"
                            stats['errors'].append(error_msg)
                            logger.error(error_msg)
                    else:
                        # 不匹配筛选条件，保留
                        stats['skipped'] += 1
                        logger.info(f"图片不匹配筛选条件，保留: image_id={image.id}, path={image_path}")
                    
                    stats['processed'] += 1
                    
                except Exception as e:
                    error_msg = f"处理图片失败 image_id={image.id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    stats['errors'].append(error_msg)
                    stats['skipped'] += 1
                    continue
            
            # 更新任务状态（如果任务没有被重置）
            db.session.refresh(task)
            if task.status == 'running':
                task.status = 'completed'
                task.finished_at = datetime.now()
                task.processed_count = stats['processed']
                if stats['errors']:
                    task.last_error = f"部分图片处理失败: {len(stats['errors'])} 个错误"
                db.session.commit()
            else:
                logger.info(f"任务状态已变为 {task.status}，跳过完成状态更新: task_id={task_id}")
            
            # 刷新任务对象以确保状态已保存
            db.session.refresh(task)
            
            # 更新需求关联任务状态
            try:
                from app.api.requirement import check_and_update_requirement_task_status
                logger.info(f"开始更新需求任务状态: cleaning, task_id={task_id}, task.status={task.status}")
                check_and_update_requirement_task_status('cleaning', task_id)
                logger.info(f"需求任务状态更新完成: cleaning, task_id={task_id}")
            except Exception as e:
                logger.error(f"更新需求任务状态失败: {e}", exc_info=True)
            
            logger.info(f"清洗任务完成 {task_id}: {stats}")
            
            return {
                'success': True,
                'message': '清洗任务执行完成',
                'stats': stats
            }
            
        except Exception as e:
            # 更新任务状态为失败（如果任务没有被重置）
            try:
                task = DataCleaningTask.query.get(task_id)
                if task:
                    db.session.refresh(task)
                    # 只有在任务仍然是running状态时才标记为失败
                    if task.status == 'running':
                        task.status = 'failed'
                        task.last_error = str(e)
                        task.finished_at = datetime.now()
                        db.session.commit()
                        
                        # 刷新任务对象以确保状态已保存
                        db.session.refresh(task)
                        
                        # 更新需求关联任务状态
                        try:
                            from app.api.requirement import check_and_update_requirement_task_status
                            logger.info(f"开始更新需求任务状态（失败）: cleaning, task_id={task_id}, task.status={task.status}")
                            check_and_update_requirement_task_status('cleaning', task_id)
                            logger.info(f"需求任务状态更新完成（失败）: cleaning, task_id={task_id}")
                        except Exception as update_error:
                            logger.error(f"更新需求任务状态失败: {update_error}", exc_info=True)
                    else:
                        logger.info(f"任务状态已变为 {task.status}，跳过失败状态更新: task_id={task_id}")
            except:
                pass
            
            error_msg = f"执行清洗任务失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'message': error_msg
            }

