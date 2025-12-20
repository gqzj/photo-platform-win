from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.requirement import Requirement
from datetime import datetime
import json
import traceback
import logging

bp = Blueprint('requirement', __name__)
logger = logging.getLogger(__name__)

@bp.route('', methods=['GET'])
def get_requirement_list():
    """获取需求列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        status = request.args.get('status', type=str)
        requester = request.args.get('requester', type=str)
        keyword = request.args.get('keyword', type=str)
        
        query = Requirement.query
        
        if status:
            query = query.filter(Requirement.status == status)
        if requester:
            query = query.filter(Requirement.requester.like(f'%{requester}%'))
        if keyword:
            query = query.filter(Requirement.name.like(f'%{keyword}%'))
        
        total = query.count()
        requirements = query.order_by(Requirement.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [req.to_dict() for req in requirements],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Error in get_requirement_list: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>', methods=['GET'])
def get_requirement_detail(requirement_id):
    """获取需求详情"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': requirement.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Error in get_requirement_detail: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_requirement():
    """创建需求"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '需求名称为必填项'}), 400
        
        # 处理JSON字段
        keywords_json = None
        if data.get('keywords'):
            keywords_json = json.dumps(data['keywords'], ensure_ascii=False) if isinstance(data['keywords'], list) else data['keywords']
        
        cleaning_features_json = None
        if data.get('cleaning_features'):
            cleaning_features_json = json.dumps(data['cleaning_features'], ensure_ascii=False) if not isinstance(data['cleaning_features'], str) else data['cleaning_features']
        
        tagging_features_json = None
        if data.get('tagging_features'):
            tagging_features_json = json.dumps(data['tagging_features'], ensure_ascii=False) if isinstance(data['tagging_features'], list) else data['tagging_features']
        
        sample_set_features_json = None
        if data.get('sample_set_features'):
            sample_set_features_json = json.dumps(data['sample_set_features'], ensure_ascii=False) if not isinstance(data['sample_set_features'], str) else data['sample_set_features']
        
        requirement = Requirement(
            name=data['name'],
            requester=data.get('requester', ''),
            keywords_json=keywords_json,
            cleaning_features_json=cleaning_features_json,
            tagging_features_json=tagging_features_json,
            sample_set_features_json=sample_set_features_json,
            status=data.get('status', 'pending'),
            note=data.get('note', ''),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(requirement)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': requirement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"Error in create_requirement: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>', methods=['PUT'])
def update_requirement(requirement_id):
    """更新需求"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        data = request.get_json()
        
        if 'name' in data:
            requirement.name = data['name']
        if 'requester' in data:
            requirement.requester = data['requester']
        if 'status' in data:
            requirement.status = data['status']
        if 'note' in data:
            requirement.note = data['note']
        
        # 处理JSON字段
        if 'keywords' in data:
            if data['keywords']:
                requirement.keywords_json = json.dumps(data['keywords'], ensure_ascii=False) if isinstance(data['keywords'], list) else data['keywords']
            else:
                requirement.keywords_json = None
        
        if 'cleaning_features' in data:
            if data['cleaning_features']:
                requirement.cleaning_features_json = json.dumps(data['cleaning_features'], ensure_ascii=False) if not isinstance(data['cleaning_features'], str) else data['cleaning_features']
            else:
                requirement.cleaning_features_json = None
        
        if 'tagging_features' in data:
            if data['tagging_features']:
                requirement.tagging_features_json = json.dumps(data['tagging_features'], ensure_ascii=False) if isinstance(data['tagging_features'], list) else data['tagging_features']
            else:
                requirement.tagging_features_json = None
        
        if 'sample_set_features' in data:
            if data['sample_set_features']:
                requirement.sample_set_features_json = json.dumps(data['sample_set_features'], ensure_ascii=False) if not isinstance(data['sample_set_features'], str) else data['sample_set_features']
            else:
                requirement.sample_set_features_json = None
        
        requirement.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': requirement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"Error in update_requirement: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>', methods=['DELETE'])
def delete_requirement(requirement_id):
    """删除需求"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        db.session.delete(requirement)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"Error in delete_requirement: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

