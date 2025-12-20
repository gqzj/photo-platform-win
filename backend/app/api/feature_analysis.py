# -*- coding: utf-8 -*-
"""
特征分析API
用于统计图片库的特征数据
"""
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.feature import Feature
from app.models.image_tagging_result import ImageTaggingResult
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
        
        # 统计有打标结果的图片数
        total_tagged_images = db.session.query(
            func.count(distinct(ImageTaggingResult.image_id))
        ).scalar() or 0
        
        # 统计总打标记录数
        total_tagging_records = ImageTaggingResult.query.count()
        
        # 统计每个特征的信息
        feature_statistics = []
        
        for feature in features:
            # 获取该特征的所有打标结果
            tagging_results = ImageTaggingResult.query.filter_by(
                feature_id=feature.id
            ).all()
            
            # 统计该特征的图片数（去重）
            tagged_image_count = db.session.query(
                func.count(distinct(ImageTaggingResult.image_id))
            ).filter_by(
                feature_id=feature.id
            ).scalar() or 0
            
            # 统计该特征的不同值数量
            distinct_values = db.session.query(
                func.count(distinct(ImageTaggingResult.tagging_value))
            ).filter_by(
                feature_id=feature.id
            ).filter(
                ImageTaggingResult.tagging_value.isnot(None),
                ImageTaggingResult.tagging_value != ''
            ).scalar() or 0
            
            # 统计该特征的总记录数
            total_records = len(tagging_results)
            
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
        
        # 统计每个特征值的图片数量
        # 使用子查询获取每个图片每个特征的最新打标结果
        from sqlalchemy.orm import aliased
        
        subquery = db.session.query(
            ImageTaggingResult.image_id,
            func.max(ImageTaggingResult.updated_at).label('max_updated_at')
        ).filter_by(
            feature_id=feature_id
        ).group_by(
            ImageTaggingResult.image_id
        ).subquery()
        
        # 获取最新的打标结果
        latest_results = db.session.query(
            ImageTaggingResult.tagging_value,
            func.count(ImageTaggingResult.image_id).label('image_count')
        ).join(
            subquery,
            db.and_(
                ImageTaggingResult.image_id == subquery.c.image_id,
                ImageTaggingResult.feature_id == feature_id,
                ImageTaggingResult.updated_at == subquery.c.max_updated_at
            )
        ).filter(
            ImageTaggingResult.tagging_value.isnot(None),
            ImageTaggingResult.tagging_value != ''
        ).group_by(
            ImageTaggingResult.tagging_value
        ).order_by(
            func.count(ImageTaggingResult.image_id).desc()
        ).all()
        
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

