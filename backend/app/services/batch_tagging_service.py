# -*- coding: utf-8 -*-
"""
批量打标服务
用于执行打标任务，批量处理图片
"""
import os
import json
import logging
import threading
from typing import Dict, List
from app.database import db
from app.models.image import Image
from app.models.tagging_task import TaggingTask
from app.models.feature import Feature
from app.models.image_tagging_result import ImageTaggingResult
from app.services.image_tagging_service import ImageTaggingService
from app.utils.config_manager import get_local_image_dir

logger = logging.getLogger(__name__)

class BatchTaggingService:
    """批量打标服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.tagging_service = ImageTaggingService()
    
    def _get_image_absolute_path(self, image: Image) -> str:
        """
        获取图片的绝对路径
        
        Args:
            image: 图片对象
            
        Returns:
            str: 图片绝对路径，如果不存在则返回None
        """
        try:
            # 从config.json获取基础存储路径
            base_path = get_local_image_dir()
            
            # 如果storage_path是相对路径，拼接基础路径
            if image.storage_path:
                # 规范化路径分隔符（兼容Windows和Linux）
                # 将数据库中的路径统一转换为当前系统的路径分隔符
                normalized_storage_path = os.path.normpath(image.storage_path.replace('/', os.sep).replace('\\', os.sep))
                
                if os.path.isabs(normalized_storage_path):
                    image_path = normalized_storage_path
                else:
                    # 尝试多种可能的路径
                    possible_paths = []
                    
                    # 1. 相对于config.json中配置的基础路径（主要路径）
                    possible_paths.append(os.path.join(base_path, normalized_storage_path))
                    
                    # 2. 如果原始路径包含正斜杠，也尝试使用原始路径拼接
                    if '/' in image.storage_path and normalized_storage_path != image.storage_path:
                        possible_paths.append(os.path.join(base_path, image.storage_path))
                    
                    # 尝试每个可能的路径
                    for path in possible_paths:
                        # 规范化路径
                        normalized_path = os.path.normpath(path)
                        if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
                            return normalized_path
                    
                    # 如果所有路径都不存在，记录警告
                    logger.warning(f"图片文件不存在，尝试过的路径: {possible_paths}, image_id={image.id}, storage_path={image.storage_path}, base_path={base_path}")
                    return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取图片路径失败 image_id={image.id}: {e}", exc_info=True)
            return None
    
    def execute_tagging_task(self, task_id: int) -> Dict:
        """
        执行打标任务
        
        Args:
            task_id: 打标任务ID
            
        Returns:
            Dict: 执行结果
        """
        try:
            # 获取任务
            task = TaggingTask.query.get(task_id)
            if not task:
                return {
                    'success': False,
                    'message': f'任务不存在: {task_id}'
                }
            
            # 检查任务状态
            if task.status == 'running':
                return {
                    'success': False,
                    'message': '任务正在执行中，请勿重复执行'
                }
            
            # 更新任务状态
            task.status = 'running'
            task.started_at = db.func.now()
            db.session.commit()
            
            # 获取任务配置
            tagging_features = []
            if task.tagging_features:
                try:
                    feature_ids = json.loads(task.tagging_features) if isinstance(task.tagging_features, str) else task.tagging_features
                    features = Feature.query.filter(Feature.id.in_(feature_ids), Feature.enabled == True).all()
                    tagging_features = [f.to_dict() for f in features]
                except Exception as e:
                    logger.error(f"解析打标特征失败: {e}")
                    task.status = 'failed'
                    task.last_error = f'解析打标特征失败: {str(e)}'
                    db.session.commit()
                    return {
                        'success': False,
                        'message': f'解析打标特征失败: {str(e)}'
                    }
            
            if not tagging_features:
                task.status = 'failed'
                task.last_error = '没有有效的打标特征'
                db.session.commit()
                return {
                    'success': False,
                    'message': '没有有效的打标特征'
                }
            
            # 获取筛选条件
            filter_keywords = []
            if task.filter_keywords:
                try:
                    filter_keywords = json.loads(task.filter_keywords) if isinstance(task.filter_keywords, str) else task.filter_keywords
                except Exception as e:
                    logger.warning(f"解析筛选关键字失败: {e}")
            
            # 查询符合条件的图片
            query = Image.query.filter(Image.status == 'active')
            
            if filter_keywords:
                # 如果有关键字筛选，使用OR条件
                keyword_filters = db.or_(*[Image.keyword.like(f'%{kw}%') for kw in filter_keywords])
                query = query.filter(keyword_filters)
            
            images = query.all()
            total_count = len(images)
            
            logger.info(f"打标任务 {task_id}: 找到 {total_count} 张符合条件的图片")
            
            # 更新任务总数
            task.total_count = total_count
            task.processed_count = 0
            db.session.commit()
            
            # 统计信息
            stats = {
                'total': total_count,
                'processed': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'errors': []
            }
            
            # 处理每张图片
            for idx, image in enumerate(images):
                try:
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
                    logger.info(f"[{idx + 1}/{total_count}] 开始打标图片: image_id={image.id}, path={image_path}")
                    
                    # 调用打标服务
                    tagging_result = self.tagging_service.tag_image(image_path, tagging_features)
                    
                    if not tagging_result['success']:
                        stats['failed'] += 1
                        error_msg = tagging_result.get('error', '未知错误')
                        stats['errors'].append({
                            'image_id': image.id,
                            'error': error_msg
                        })
                        logger.error(f"图片打标失败: image_id={image.id}, error={error_msg}")
                        continue
                    
                    # 保存打标结果
                    result_data = tagging_result['result']
                    
                    # 为每个特征保存一条记录
                    for feature in tagging_features:
                        feature_id = feature['id']
                        feature_name = feature['name']
                        
                        # 获取该特征的值
                        feature_value = result_data.get(feature_name, None)
                        
                        # 检查是否已存在记录
                        existing_result = ImageTaggingResult.query.filter_by(
                            tagging_task_id=task_id,
                            image_id=image.id,
                            feature_id=feature_id
                        ).first()
                        
                        if existing_result:
                            # 更新现有记录
                            existing_result.tagging_value = str(feature_value) if feature_value is not None else None
                            existing_result.tagging_result_json = json.dumps(result_data, ensure_ascii=False)
                            existing_result.updated_at = db.func.now()
                        else:
                            # 创建新记录
                            new_result = ImageTaggingResult(
                                tagging_task_id=task_id,
                                image_id=image.id,
                                feature_id=feature_id,
                                tagging_value=str(feature_value) if feature_value is not None else None,
                                tagging_result_json=json.dumps(result_data, ensure_ascii=False)
                            )
                            db.session.add(new_result)
                    
                    # 提交数据库更改
                    db.session.commit()
                    stats['success'] += 1
                    stats['processed'] += 1
                    
                    logger.info(f"图片打标成功: image_id={image.id}")
                    
                except Exception as e:
                    stats['failed'] += 1
                    stats['processed'] += 1
                    error_msg = str(e)
                    stats['errors'].append({
                        'image_id': image.id if 'image' in locals() else None,
                        'error': error_msg
                    })
                    logger.error(f"处理图片失败: {e}", exc_info=True)
                    db.session.rollback()
            
            # 更新任务状态
            task.status = 'completed'
            task.finished_at = db.func.now()
            task.processed_count = stats['processed']
            if stats['errors']:
                task.last_error = json.dumps(stats['errors'][:10], ensure_ascii=False)  # 只保存前10个错误
            db.session.commit()
            
            logger.info(f"打标任务完成 {task_id}: {stats}")
            
            return {
                'success': True,
                'message': '打标任务执行完成',
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"执行打标任务失败 {task_id}: {e}", exc_info=True)
            
            # 更新任务状态为失败
            try:
                task = TaggingTask.query.get(task_id)
                if task:
                    task.status = 'failed'
                    task.last_error = str(e)
                    task.finished_at = db.func.now()
                    db.session.commit()
            except:
                pass
            
            return {
                'success': False,
                'message': f'执行打标任务失败: {str(e)}'
            }

