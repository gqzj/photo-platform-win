# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.keyword_statistics import KeywordStatistics
from app.models.image import Image
from sqlalchemy import func
import traceback

bp = Blueprint('keyword_statistics', __name__)

@bp.route('', methods=['GET'])
def get_keyword_statistics():
    """获取关键字统计列表"""
    try:
        # 实时统计关键字（不依赖汇总表，直接从images表统计）
        query = db.session.query(
            Image.keyword,
            func.count(Image.id).label('image_count')
        ).filter(
            Image.keyword.isnot(None),
            Image.keyword != ''
        ).group_by(Image.keyword).order_by(func.count(Image.id).desc())
        
        results = query.all()
        
        keywords = []
        for keyword, count in results:
            keywords.append({
                'keyword': keyword,
                'image_count': count
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': keywords,
                'total': len(keywords)
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取关键字统计失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/refresh', methods=['POST'])
def refresh_keyword_statistics():
    """刷新关键字统计数据"""
    try:
        # 清空现有数据
        KeywordStatistics.query.delete()
        
        # 从images表统计关键字
        results = db.session.query(
            Image.keyword,
            func.count(Image.id).label('image_count')
        ).filter(
            Image.keyword.isnot(None),
            Image.keyword != ''
        ).group_by(Image.keyword).all()
        
        # 批量插入
        keyword_stats = []
        for keyword, count in results:
            keyword_stat = KeywordStatistics(
                keyword=keyword,
                image_count=count
            )
            keyword_stats.append(keyword_stat)
        
        if keyword_stats:
            db.session.bulk_save_objects(keyword_stats)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功刷新 {len(keyword_stats)} 个关键字统计',
            'data': {
                'count': len(keyword_stats)
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"刷新关键字统计失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

