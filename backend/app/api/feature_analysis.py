# -*- coding: utf-8 -*-
"""
特征分析API
用于统计图片库的特征数据
"""
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.feature import Feature
from app.models.image_tagging_result import ImageTaggingResult
from app.models.image_tagging_result_detail import ImageTaggingResultDetail
from app.models.image import Image
from sqlalchemy import func, distinct
import traceback

bp = Blueprint('feature_analysis', __name__)

@bp.route('/statistics', methods=['GET'])
def get_feature_statistics():
    """获取特征统计信息"""
    try:
        # 获取所有启用的特征
        features = Feature.query.filter_by(enabled=True).all()
        
        # 统计总体信息
        total_features = len(features)
        
        # 统计有打标结果的图片数（从汇总表）
        total_tagged_images = ImageTaggingResult.query.count()
        
        # 统计总打标记录数（从明细表）
        total_tagging_records = ImageTaggingResultDetail.query.count()
        
        # 统计每个特征的信息
        feature_statistics = []
        
        for feature in features:
            # 统计该特征的图片数（从明细表查询）
            tagged_image_count = db.session.query(
                func.count(distinct(ImageTaggingResultDetail.image_id))
            ).filter_by(
                feature_id=feature.id
            ).scalar() or 0
            
            # 统计该特征的不同值数量（从明细表查询）
            distinct_values = db.session.query(
                func.count(distinct(ImageTaggingResultDetail.tagging_value))
            ).filter_by(
                feature_id=feature.id
            ).filter(
                ImageTaggingResultDetail.tagging_value.isnot(None),
                ImageTaggingResultDetail.tagging_value != ''
            ).scalar() or 0
            
            # 统计该特征的总记录数（从明细表）
            total_records = ImageTaggingResultDetail.query.filter_by(
                feature_id=feature.id
            ).count()
            
            feature_statistics.append({
                'feature_id': feature.id,
                'feature_name': feature.name,
                'feature_category': feature.category,
                'tagged_image_count': tagged_image_count,
                'distinct_value_count': distinct_values,
                'total_records': total_records
            })
        
        # 按打标图片数排序
        feature_statistics.sort(key=lambda x: x['tagged_image_count'], reverse=True)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_features': total_features,
                'total_tagged_images': total_tagged_images,
                'total_tagging_records': total_tagging_records,
                'feature_statistics': feature_statistics
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征统计失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/feature/<int:feature_id>/distribution', methods=['GET'])
def get_feature_value_distribution(feature_id):
    """获取指定特征的值分布"""
    try:
        # 验证特征是否存在
        feature = Feature.query.get(feature_id)
        if not feature:
            return jsonify({
                'code': 404,
                'message': '特征不存在'
            }), 404
        
        # 统计每个特征值的图片数量（从明细表直接查询）
        value_distribution = db.session.query(
            ImageTaggingResultDetail.tagging_value,
            func.count(ImageTaggingResultDetail.image_id).label('image_count')
        ).filter_by(
            feature_id=feature_id
        ).filter(
            ImageTaggingResultDetail.tagging_value.isnot(None),
            ImageTaggingResultDetail.tagging_value != ''
        ).group_by(
            ImageTaggingResultDetail.tagging_value
        ).order_by(
            func.count(ImageTaggingResultDetail.image_id).desc()
        ).all()
        
        latest_results = value_distribution
        
        # 转换为列表格式
        distribution = []
        total_count = 0
        for value, count in latest_results:
            distribution.append({
                'value': value,
                'count': count,
                'percentage': 0  # 稍后计算
            })
            total_count += count
        
        # 计算百分比
        for item in distribution:
            if total_count > 0:
                item['percentage'] = round(item['count'] / total_count * 100, 2)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'feature_id': feature.id,
                'feature_name': feature.name,
                'total_images': total_count,
                'distribution': distribution
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征值分布失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

