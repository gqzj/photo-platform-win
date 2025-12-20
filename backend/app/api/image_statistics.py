from flask import Blueprint, request, jsonify
from app.database import db
from app.models.image import Image
from sqlalchemy import func
import json

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
