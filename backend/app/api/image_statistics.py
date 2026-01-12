from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.image import Image
from app.models.feature import Feature
from app.models.image_tagging_result_detail import ImageTaggingResultDetail
from sqlalchemy import func
import json
import traceback

bp = Blueprint('image_statistics', __name__)

@bp.route('', methods=['GET'])
def get_statistics():
    """获取统计数据"""
    try:
        # 总图片数
        total_images = Image.query.filter_by(status='active').count()
        
        # 已打标图片数（hash_tags_json不为空）
        tagged_images = Image.query.filter(
            Image.status == 'active',
            Image.hash_tags_json.isnot(None),
            Image.hash_tags_json != ''
        ).count()
        
        # 今日抓取数
        from datetime import date
        today = date.today()
        today_captured = Image.query.filter(
            func.date(Image.created_at) == today,
            Image.status == 'active'
        ).count()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_images': total_images,
                'tagged_images': tagged_images,
                'today_captured': today_captured
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/tags', methods=['GET'])
def get_tag_statistics():
    """获取标签统计"""
    try:
        # 统计每个标签的图片数量（从hash_tags_json中提取）
        images = Image.query.filter(
            Image.status == 'active',
            Image.hash_tags_json.isnot(None),
            Image.hash_tags_json != ''
        ).all()
        
        tag_count = {}
        for image in images:
            try:
                tags = json.loads(image.hash_tags_json)
                if isinstance(tags, list):
                    for tag in tags:
                        tag_count[tag] = tag_count.get(tag, 0) + 1
            except:
                continue
        
        result = [{'tag_name': tag, 'count': count} for tag, count in tag_count.items()]
        result.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/trend', methods=['GET'])
def get_time_trend():
    """获取时间趋势"""
    try:
        # 按日期统计图片数量
        date_stats = db.session.query(
            func.date(Image.created_at).label('date'),
            func.count(Image.id).label('count')
        ).filter(
            Image.status == 'active'
        ).group_by(func.date(Image.created_at)).order_by(func.date(Image.created_at).desc()).limit(30).all()
        
        result = [{'date': str(stat.date), 'count': stat.count} for stat in date_stats]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/features', methods=['GET'])
def get_features():
    """获取所有特征列表"""
    try:
        features = Feature.query.filter_by(enabled=True).order_by(Feature.id.desc()).all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [feature.to_dict() for feature in features]
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/feature-stats', methods=['POST'])
def get_feature_statistics():
    """获取特征统计数据
    请求体: {"feature_ids": [1, 2, 3]}
    返回: 每个特征的统计数据和汇总数据
    """
    try:
        data = request.get_json() or {}
        feature_ids = data.get('feature_ids', [])
        
        if not feature_ids:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'feature_stats': {},
                    'summary': []
                }
            })
        
        # 获取特征信息
        features = Feature.query.filter(Feature.id.in_(feature_ids)).all()
        feature_map = {f.id: f for f in features}
        
        # 统计每个特征的特征值分布
        feature_stats = {}
        summary_data = []  # 汇总数据：所有特征值及其图片数
        
        for feature_id in feature_ids:
            if feature_id not in feature_map:
                continue
            
            feature = feature_map[feature_id]
            
            # 统计该特征的特征值分布
            stats = db.session.query(
                ImageTaggingResultDetail.tagging_value,
                func.count(ImageTaggingResultDetail.image_id).label('count')
            ).filter(
                ImageTaggingResultDetail.feature_id == feature_id
            ).group_by(
                ImageTaggingResultDetail.tagging_value
            ).all()
            
            # 构建该特征的统计数据
            feature_stat = {
                'feature_id': feature_id,
                'feature_name': feature.name,
                'feature_color': feature.color,  # 添加特征颜色
                'values': []
            }
            
            for stat in stats:
                value = stat.tagging_value or '未标注'
                count = stat.count
                feature_stat['values'].append({
                    'value': value,
                    'count': count
                })
                # 添加到汇总数据
                summary_data.append({
                    'feature_id': feature_id,
                    'feature_name': feature.name,
                    'feature_color': feature.color,  # 添加特征颜色
                    'value': value,
                    'count': count
                })
            
            # 按数量降序排序
            feature_stat['values'].sort(key=lambda x: x['count'], reverse=True)
            feature_stats[feature_id] = feature_stat
        
        # 汇总数据按数量降序排序
        summary_data.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'feature_stats': feature_stats,
                'summary': summary_data
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取特征统计失败: {traceback.format_exc()}")
        return jsonify({'code': 500, 'message': str(e)}), 500
