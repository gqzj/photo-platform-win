from flask import Blueprint, request, jsonify
from app.database import db
from app.models.image import Image
from datetime import datetime

bp = Blueprint('image_capture', __name__)

@bp.route('', methods=['GET'])
def get_capture_list():
    """获取抓取列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        
        query = Image.query.filter_by(status='active')
        total = query.count()
        
        images = query.order_by(Image.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [img.to_dict() for img in images],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/start', methods=['POST'])
def start_capture():
    """开始抓取"""
    try:
        data = request.get_json()
        # TODO: 实现图片抓取逻辑
        return jsonify({
            'code': 200,
            'message': '抓取任务已启动',
            'data': None
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/pause', methods=['POST'])
def pause_capture():
    """暂停抓取"""
    try:
        # TODO: 实现暂停逻辑
        return jsonify({
            'code': 200,
            'message': '抓取任务已暂停',
            'data': None
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/stop', methods=['POST'])
def stop_capture():
    """停止抓取"""
    try:
        # TODO: 实现停止逻辑
        return jsonify({
            'code': 200,
            'message': '抓取任务已停止',
            'data': None
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

