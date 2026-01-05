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
from app.models.image_tagging_result_detail import ImageTaggingResultDetail

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
            
            # 获取关键字列表
            keywords = []
            if sample_set.keywords_json:
                try:
                    keywords = json.loads(sample_set.keywords_json) if isinstance(sample_set.keywords_json, str) else sample_set.keywords_json
                    if not isinstance(keywords, list):
                        keywords = []
                except:
                    keywords = []
            
            # 获取所有有打标结果的图片（只查询配置的特征）
            # 从明细表直接查询，每个图片每个特征只有一条记录（最新的）
            tagging_details = ImageTaggingResultDetail.query.filter(
                ImageTaggingResultDetail.feature_id.in_(feature_ids)
            ).all()
            
            # 如果有关键字筛选，需要先获取符合条件的图片ID
            image_ids_filter = None
            if keywords:
                from sqlalchemy import or_
                # 查询关键字匹配的图片
                keyword_images = Image.query.filter(
                    Image.status == 'active',
                    or_(*[Image.keyword.like(f'%{kw}%') for kw in keywords if kw])
                ).all()
                image_ids_filter = set([img.id for img in keyword_images])
                logger.info(f"关键字筛选: {keywords}, 匹配到 {len(image_ids_filter)} 张图片")
            
            # 按图片ID分组打标结果
            image_tagging_map = {}
            for detail in tagging_details:
                image_id = detail.image_id
                if image_id not in image_tagging_map:
                    image_tagging_map[image_id] = {}
                image_tagging_map[image_id][detail.feature_id] = detail.tagging_value
            
            # 清空旧的样本集图片数据
            SampleSetImage.query.filter_by(sample_set_id=sample_set_id).delete()
            
            # 统计匹配的图片
            matched_images = []
            matched_count = 0
            
            # 遍历所有有打标结果的图片
            for image_id, tagging_values in image_tagging_map.items():
                # 如果有关键字筛选，先检查图片是否在筛选范围内
                if image_ids_filter is not None and image_id not in image_ids_filter:
                    continue
                
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

