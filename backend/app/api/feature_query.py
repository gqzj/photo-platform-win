# -*- coding: utf-8 -*-
"""
特征组合查询API
根据特征和特征值组合查询图片
"""
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.image import Image
from app.models.image_tagging_result_detail import ImageTaggingResultDetail
from app.models.feature import Feature
import traceback
from sqlalchemy import and_

bp = Blueprint('feature_query', __name__)

def _match_images_by_feature_values(feature_values_dict, feature_name_to_id):
    """
    根据特征值组合匹配图片
    
    Args:
        feature_values_dict: 特征值组合字典，格式：{"特征名": ["特征值1", "特征值2"]}
        feature_name_to_id: 特征名称到特征ID的映射
    
    Returns:
        匹配的图片ID列表
    """
    try:
        # 构建查询条件：每个特征都需要匹配（AND关系）
        # 对于每个特征，只要匹配到任意一个特征值即可（OR关系）
        
        image_id_sets = []
        
        for feature_name, feature_values in feature_values_dict.items():
            feature_id = feature_name_to_id.get(feature_name)
            if not feature_id:
                current_app.logger.warning(f"特征 {feature_name} 没有找到对应的特征ID")
                continue
            
            # 查询该特征的任意一个特征值匹配的图片（OR关系）
            matching_details = ImageTaggingResultDetail.query.filter(
                ImageTaggingResultDetail.feature_id == feature_id,
                ImageTaggingResultDetail.tagging_value.in_([str(v) for v in feature_values])
            ).all()
            
            image_ids = {detail.image_id for detail in matching_details}
            if image_ids:
                image_id_sets.append(image_ids)
                current_app.logger.debug(f"特征 {feature_name} (值: {feature_values}) 匹配到 {len(image_ids)} 张图片")
            else:
                current_app.logger.debug(f"特征 {feature_name} (值: {feature_values}) 没有匹配到图片")
        
        if not image_id_sets:
            return []
        
        # 取交集：所有特征条件都满足的图片（AND关系）
        matched_image_ids = set(image_id_sets[0])
        for image_id_set in image_id_sets[1:]:
            matched_image_ids = matched_image_ids & image_id_set
        
        if not matched_image_ids:
            return []
        
        # 过滤掉已删除的图片
        active_images = Image.query.filter(
            Image.id.in_(list(matched_image_ids)),
            Image.status == 'active'
        ).all()
        active_image_ids = [img.id for img in active_images]
        
        current_app.logger.info(f"特征值组合 {feature_values_dict} 匹配到 {len(active_image_ids)} 张有效图片")
        
        return active_image_ids
        
    except Exception as e:
        current_app.logger.error(f"匹配图片失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return []

@bp.route('/search', methods=['POST'])
def search_images_by_features():
    """根据特征和特征值组合查询图片"""
    try:
        data = request.get_json()
        
        # 验证输入数据
        if not data or 'features' not in data:
            return jsonify({'code': 400, 'message': '请提供特征和特征值'}), 400
        
        features_data = data.get('features', [])
        if not features_data or not isinstance(features_data, list):
            return jsonify({'code': 400, 'message': '特征数据格式错误'}), 400
        
        # 获取特征ID映射
        feature_name_to_id = {}
        validated_features = {}
        
        for feature_item in features_data:
            feature_id = feature_item.get('feature_id')
            if not feature_id:
                return jsonify({'code': 400, 'message': '特征ID不能为空'}), 400
            
            feature = Feature.query.get(feature_id)
            if not feature:
                return jsonify({'code': 400, 'message': f'特征ID {feature_id} 不存在'}), 400
            
            if not feature.enabled:
                return jsonify({'code': 400, 'message': f'特征 {feature.name} 已禁用，不能使用'}), 400
            
            feature_values = feature_item.get('values', [])
            if not feature_values or not isinstance(feature_values, list) or len(feature_values) == 0:
                return jsonify({'code': 400, 'message': f'特征 {feature.name} 至少需要选择一个特征值'}), 400
            
            feature_name_to_id[feature.name] = feature.id
            validated_features[feature.name] = feature_values
        
        # 匹配图片
        matched_image_ids = _match_images_by_feature_values(validated_features, feature_name_to_id)
        
        # 分页参数
        page = data.get('page', 1)
        page_size = data.get('page_size', 20)
        
        # 查询图片详情
        if not matched_image_ids:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'list': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size
                }
            })
        
        # 分页查询
        total = len(matched_image_ids)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_image_ids = matched_image_ids[start_idx:end_idx]
        
        images = Image.query.filter(Image.id.in_(page_image_ids)).all()
        
        # 保持顺序
        image_dict = {img.id: img for img in images}
        ordered_images = [image_dict[img_id] for img_id in page_image_ids if img_id in image_dict]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [img.to_dict() for img in ordered_images],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"特征组合查询失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
