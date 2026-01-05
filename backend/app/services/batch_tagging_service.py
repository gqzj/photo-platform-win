# -*- coding: utf-8 -*-
"""
批量打标服务
用于执行打标任务，批量处理图片
"""
import os
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List
from app.database import db
from app.models.image import Image
from app.models.tagging_task import TaggingTask
from app.models.feature import Feature
from app.models.image_tagging_result import ImageTaggingResult
from app.models.image_tagging_result_detail import ImageTaggingResultDetail
from app.models.image_tagging_result_history import ImageTaggingResultHistory
from app.services.image_tagging_service import ImageTaggingService
from app.utils.config_manager import get_local_image_dir
from sqlalchemy import func

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
            
            # 如果任务是被中断的，从上次中断的位置继续
            start_index = 0
            if task.status == 'interrupted':
                # 从已处理的图片数继续
                start_index = task.processed_count
                logger.info(f"重启中断的任务: task_id={task_id}, 从第 {start_index + 1} 张图片开始")
            
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
            
            # 更新任务总数（如果是重启中断的任务，保持总数不变）
            if task.status != 'interrupted':
                task.total_count = total_count
                task.processed_count = 0
            else:
                # 重启中断的任务，确保总数一致
                task.total_count = total_count
            task.status = 'running'
            task.started_at = db.func.now()
            task.finished_at = None
            task.last_error = None
            db.session.commit()
            
            # 统计信息（如果是重启中断的任务，需要从已有数据中恢复统计）
            stats = {
                'total': total_count,
                'processed': start_index,
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'errors': []
            }
            
            # 如果是重启中断的任务，统计已处理的成功和失败数量（可选，用于显示）
            if start_index > 0:
                logger.info(f"重启中断的任务，已处理 {start_index} 张图片，继续处理剩余 {total_count - start_index} 张")
            
            # 处理每张图片（从start_index开始）
            for idx, image in enumerate(images[start_index:], start=start_index):
                try:
                    # 检查任务是否被中断（每次循环都检查）
                    task = TaggingTask.query.get(task_id)
                    if not task or task.status == 'interrupted':
                        logger.info(f"打标任务被中断: task_id={task_id}, 已处理 {idx}/{total_count} 张图片")
                        # 更新任务状态
                        if task:
                            task.status = 'interrupted'
                            task.finished_at = db.func.now()
                            task.last_error = '任务被用户中断'
                            db.session.commit()
                        return {
                            'success': False,
                            'message': '任务已被中断',
                            'stats': stats
                        }
                    
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
                    
                    # 检查历史记录，看是否有该图片该特征的打标结果可以复用
                    feature_ids = [f['id'] for f in tagging_features]
                    
                    # 查询历史记录：每个图片每个特征的最新打标结果（排除当前任务）
                    # 使用子查询获取每个特征的最新记录
                    history_subquery = db.session.query(
                        ImageTaggingResultHistory.feature_id,
                        func.max(ImageTaggingResultHistory.created_at).label('max_created_at')
                    ).filter(
                        ImageTaggingResultHistory.image_id == image.id,
                        ImageTaggingResultHistory.feature_id.in_(feature_ids),
                        ImageTaggingResultHistory.tagging_task_id != task_id
                    ).group_by(
                        ImageTaggingResultHistory.feature_id
                    ).subquery()
                    
                    history_records = db.session.query(ImageTaggingResultHistory).join(
                        history_subquery,
                        db.and_(
                            ImageTaggingResultHistory.feature_id == history_subquery.c.feature_id,
                            ImageTaggingResultHistory.created_at == history_subquery.c.max_created_at,
                            ImageTaggingResultHistory.image_id == image.id,
                            ImageTaggingResultHistory.tagging_task_id != task_id
                        )
                    ).all()
                    
                    # 构建历史记录映射：feature_id -> {tagging_value, source_task_id}
                    history_map = {}
                    for hist in history_records:
                        # source_task_id：如果历史记录有source_task_id，说明是复用的，使用source_task_id；否则使用tagging_task_id（原始打标）
                        source_task_id = hist.source_task_id if hist.source_task_id else hist.tagging_task_id
                        history_map[hist.feature_id] = {
                            'tagging_value': hist.tagging_value,
                            'source_task_id': source_task_id,
                            'history_record': hist  # 保存历史记录对象，用于后续使用
                        }
                    
                    # 检查哪些特征需要重新打标，哪些可以复用
                    features_to_tag = []  # 需要打标的特征
                    features_reused = {}  # 可以复用的特征 {feature_id: {tagging_value, source_task_id}}
                    
                    for feature in tagging_features:
                        feature_id = feature['id']
                        if feature_id in history_map:
                            # 可以复用历史记录
                            features_reused[feature_id] = history_map[feature_id]
                            logger.info(f"复用历史打标结果: image_id={image.id}, feature_id={feature_id}, source_task_id={history_map[feature_id]['source_task_id']}")
                        else:
                            # 需要重新打标
                            features_to_tag.append(feature)
                    
                    # 如果有需要打标的特征，调用打标服务
                    result_data = {}
                    if features_to_tag:
                        # 调用打标服务（只打标需要打标的特征）
                        tagging_result = self.tagging_service.tag_image(image_path, features_to_tag)
                        
                        if not tagging_result['success']:
                            stats['failed'] += 1
                            error_msg = tagging_result.get('error', '未知错误')
                            stats['errors'].append({
                                'image_id': image.id,
                                'error': error_msg
                            })
                            logger.error(f"图片打标失败: image_id={image.id}, error={error_msg}")
                            continue
                        
                        result_data = tagging_result['result']
                    else:
                        # 所有特征都可以复用，不需要调用AI
                        logger.info(f"所有特征都复用历史记录，跳过AI打标: image_id={image.id}")
                    
                    # 合并打标结果（新打标的结果 + 复用的历史结果）
                    for feature_id, hist_data in features_reused.items():
                        feature_name = None
                        for f in tagging_features:
                            if f['id'] == feature_id:
                                feature_name = f['name']
                                break
                        if feature_name:
                            result_data[feature_name] = hist_data['tagging_value']
                    
                    result_json_str = json.dumps(result_data, ensure_ascii=False)
                    
                    # 1. 更新或创建汇总记录（image_tagging_results）
                    summary_result = ImageTaggingResult.query.filter_by(image_id=image.id).first()
                    if summary_result:
                        # 更新现有汇总记录
                        summary_result.last_tagging_task_id = task_id
                        summary_result.tagging_result_json = result_json_str
                        summary_result.updated_at = datetime.now()
                    else:
                        # 创建新汇总记录
                        summary_result = ImageTaggingResult(
                            image_id=image.id,
                            last_tagging_task_id=task_id,
                            tagging_result_json=result_json_str
                        )
                        db.session.add(summary_result)
                    
                    # 2. 为每个特征保存或更新明细记录（image_tagging_results_detail）
                    for feature in tagging_features:
                        feature_id = feature['id']
                        feature_name = feature['name']
                        
                        # 获取该特征的值
                        feature_value = result_data.get(feature_name, None)
                        
                        # 判断是复用还是新打标
                        is_reused = feature_id in features_reused
                        # 如果是复用的，source_task_id是原始任务ID；如果是新打标的，source_task_id为None（表示是当前任务打标的）
                        if is_reused:
                            source_task_id = features_reused[feature_id]['source_task_id']
                        else:
                            source_task_id = None  # 新打标，没有来源任务
                        
                        # 检查是否已存在明细记录
                        existing_detail = ImageTaggingResultDetail.query.filter_by(
                            image_id=image.id,
                            feature_id=feature_id
                        ).first()
                        
                        if existing_detail:
                            # 更新现有明细记录（只更新最后打标任务ID和值）
                            existing_detail.tagging_value = str(feature_value) if feature_value is not None else None
                            existing_detail.last_tagging_task_id = task_id
                            existing_detail.updated_at = datetime.now()
                        else:
                            # 创建新明细记录
                            new_detail = ImageTaggingResultDetail(
                                image_id=image.id,
                                feature_id=feature_id,
                                tagging_value=str(feature_value) if feature_value is not None else None,
                                last_tagging_task_id=task_id
                            )
                            db.session.add(new_detail)
                        
                        # 3. 保存历史记录（image_tagging_results_history）
                        history_record = ImageTaggingResultHistory(
                            tagging_task_id=task_id,
                            image_id=image.id,
                            feature_id=feature_id,
                            tagging_value=str(feature_value) if feature_value is not None else None,
                            source_task_id=source_task_id  # 如果是复用的，记录原始任务ID
                        )
                        db.session.add(history_record)
                    
                    # 提交数据库更改
                    db.session.commit()
                    stats['success'] += 1
                    stats['processed'] += 1
                    
                    # 记录复用信息
                    if features_reused:
                        reused_count = len(features_reused)
                        logger.info(f"图片打标完成（复用 {reused_count} 个特征）: image_id={image.id}")
                    
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
            
            # 更新任务状态（如果任务没有被中断）
            task = TaggingTask.query.get(task_id)
            if task and task.status != 'interrupted':
                task.status = 'completed'
                task.finished_at = db.func.now()
                task.processed_count = stats['processed']
                if stats['errors']:
                    task.last_error = json.dumps(stats['errors'][:10], ensure_ascii=False)  # 只保存前10个错误
                db.session.commit()
                
                # 刷新任务对象以确保状态已保存
                db.session.refresh(task)
                
                # 更新需求关联任务状态
                try:
                    from app.api.requirement import check_and_update_requirement_task_status
                    logger.info(f"开始更新需求任务状态: tagging, task_id={task_id}, task.status={task.status}")
                    check_and_update_requirement_task_status('tagging', task_id)
                    logger.info(f"需求任务状态更新完成: tagging, task_id={task_id}")
                except Exception as e:
                    logger.error(f"更新需求任务状态失败: {e}", exc_info=True)
            
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
                    
                    # 刷新任务对象以确保状态已保存
                    db.session.refresh(task)
                    
                    # 更新需求关联任务状态
                    try:
                        from app.api.requirement import check_and_update_requirement_task_status
                        logger.info(f"开始更新需求任务状态（失败）: tagging, task_id={task_id}, task.status={task.status}")
                        check_and_update_requirement_task_status('tagging', task_id)
                        logger.info(f"需求任务状态更新完成（失败）: tagging, task_id={task_id}")
                    except Exception as update_error:
                        logger.error(f"更新需求任务状态失败: {update_error}", exc_info=True)
            except:
                pass
            
            return {
                'success': False,
                'message': f'执行打标任务失败: {str(e)}'
            }

