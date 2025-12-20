# -*- coding: utf-8 -*-
"""
样本集服务
用于计算样本集的实际数据
"""
import json
import logging
from typing import Dict, List, Optional
from app.database import db
from app.models.sample_set import SampleSet, SampleSetFeature, SampleSetImage
from app.models.image import Image
from app.models.image_tagging_result import ImageTaggingResult

logger = logging.getLogger(__name__)

class SampleSetService:
    """样本集服务类"""
    
    def _check_feature_match(self, tagging_value: str, feature: SampleSetFeature) -> bool:
        """
        检查打标值是否匹配特征条件
        
        Args:
            tagging_value: 图片的打标值
            feature: 样本集特征配置
            
        Returns:
            bool: 是否匹配
        """
        if not tagging_value:
            return False
        
        value_type = feature.value_type
        value_range = feature.value_range
        
        if value_type == 'any':
            # 任意值都匹配
            return True
        
        if not value_range:
            return False
        
        try:
            range_data = json.loads(value_range) if isinstance(value_range, str) else value_range
        except:
            return False
        
        if value_type == 'enum':
            # 枚举类型：值必须在列表中
            if isinstance(range_data, list):
                return str(tagging_value) in [str(v) for v in range_data]
            return False
        
        elif value_type == 'range':
            # 范围类型：值必须在范围内
            if isinstance(range_data, dict):
                min_val = range_data.get('min')
                max_val = range_data.get('max')
                try:
                    val = float(tagging_value)
                    if min_val is not None and val < min_val:
                        return False
                    if max_val is not None and val > max_val:
                        return False
                    return True
                except:
                    return False
            return False
        
        return False
    
    def calculate_sample_set_data(self, sample_set_id: int) -> Dict:
        """
        计算样本集的实际数据
        
        Args:
            sample_set_id: 样本集ID
            
        Returns:
            Dict: 计算结果
        """
        try:
            # 获取样本集
            sample_set = SampleSet.query.get(sample_set_id)
            if not sample_set:
                return {
                    'success': False,
                    'message': f'样本集不存在: {sample_set_id}'
                }
            
            # 获取样本集的特征配置
            features = SampleSetFeature.query.filter_by(sample_set_id=sample_set_id).all()
            if not features:
                return {
                    'success': False,
                    'message': '样本集没有配置特征，无法计算数据'
                }
            
            # 获取所有特征ID
            feature_ids = [f.feature_id for f in features]
            
            # 获取所有有打标结果的图片（只查询配置的特征）
            # 注意：这里查询所有打标任务的结果，因为样本集可能基于多个打标任务的结果
            # 如果一张图片有多个打标任务的结果，取最新的（按updated_at）
            from sqlalchemy import func
            from sqlalchemy.orm import aliased
            
            # 使用子查询获取每个图片每个特征的最新打标结果
            subquery = db.session.query(
                ImageTaggingResult.image_id,
                ImageTaggingResult.feature_id,
                func.max(ImageTaggingResult.updated_at).label('max_updated_at')
            ).filter(
                ImageTaggingResult.feature_id.in_(feature_ids)
            ).group_by(
                ImageTaggingResult.image_id,
                ImageTaggingResult.feature_id
            ).subquery()
            
            # 获取最新的打标结果
            latest_results = db.session.query(ImageTaggingResult).join(
                subquery,
                db.and_(
                    ImageTaggingResult.image_id == subquery.c.image_id,
                    ImageTaggingResult.feature_id == subquery.c.feature_id,
                    ImageTaggingResult.updated_at == subquery.c.max_updated_at
                )
            ).all()
            
            # 按图片ID分组打标结果
            image_tagging_map = {}
            for result in latest_results:
                image_id = result.image_id
                if image_id not in image_tagging_map:
                    image_tagging_map[image_id] = {}
                image_tagging_map[image_id][result.feature_id] = result.tagging_value
            
            # 清空旧的样本集图片数据
            SampleSetImage.query.filter_by(sample_set_id=sample_set_id).delete()
            
            # 统计匹配的图片
            matched_images = []
            matched_count = 0
            
            # 遍历所有有打标结果的图片
            for image_id, tagging_values in image_tagging_map.items():
                # 检查是否匹配所有特征条件
                all_match = True
                matched_feature_ids = []
                
                for feature in features:
                    feature_id = feature.feature_id
                    tagging_value = tagging_values.get(feature_id)
                    
                    if not self._check_feature_match(tagging_value, feature):
                        all_match = False
                        break
                    else:
                        matched_feature_ids.append(feature_id)
                
                # 如果匹配所有特征条件，添加到样本集
                if all_match:
                    matched_images.append({
                        'image_id': image_id,
                        'matched_features': matched_feature_ids
                    })
                    matched_count += 1
            
            # 批量插入样本集图片数据
            if matched_images:
                sample_set_images = []
                for item in matched_images:
                    sample_set_image = SampleSetImage(
                        sample_set_id=sample_set_id,
                        image_id=item['image_id'],
                        matched_features=json.dumps(item['matched_features'], ensure_ascii=False)
                    )
                    sample_set_images.append(sample_set_image)
                
                db.session.bulk_save_objects(sample_set_images)
            
            # 更新样本集的图片数量
            sample_set.image_count = matched_count
            
            db.session.commit()
            
            logger.info(f"样本集数据计算完成: sample_set_id={sample_set_id}, matched_count={matched_count}")
            
            return {
                'success': True,
                'message': '样本集数据计算完成',
                'matched_count': matched_count
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"计算样本集数据失败 {sample_set_id}: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'计算样本集数据失败: {str(e)}'
            }

