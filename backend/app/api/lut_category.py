# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.lut_category import LutCategory
import traceback

bp = Blueprint('lut_category', __name__)

@bp.route('', methods=['GET'])
def get_category_list():
    """获取Lut分类列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        query = LutCategory.query
        
        if keyword:
            query = query.filter(LutCategory.name.like(f'%{keyword}%'))
        
        total = query.count()
        categories = query.order_by(LutCategory.sort_order.asc(), LutCategory.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [cat.to_dict() for cat in categories],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取Lut分类列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/all', methods=['GET'])
def get_all_categories():
    """获取所有Lut分类（不分页）"""
    try:
        categories = LutCategory.query.order_by(LutCategory.sort_order.asc(), LutCategory.id.desc()).all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [cat.to_dict() for cat in categories]
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取所有Lut分类失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """获取Lut分类详情"""
    try:
        category = LutCategory.query.get_or_404(category_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取Lut分类详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_category():
    """创建Lut分类"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        sort_order = data.get('sort_order', 0)
        
        if not name:
            return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400
        
        # 检查名称是否已存在
        existing = LutCategory.query.filter_by(name=name).first()
        if existing:
            return jsonify({'code': 400, 'message': '分类名称已存在'}), 400
        
        category = LutCategory(
            name=name,
            description=description,
            sort_order=sort_order
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建Lut分类失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """更新Lut分类"""
    try:
        category = LutCategory.query.get_or_404(category_id)
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description')
        sort_order = data.get('sort_order')
        
        if name:
            # 检查名称是否已被其他分类使用
            existing = LutCategory.query.filter(LutCategory.name == name, LutCategory.id != category_id).first()
            if existing:
                return jsonify({'code': 400, 'message': '分类名称已被使用'}), 400
            category.name = name
        
        if description is not None:
            category.description = description
        
        if sort_order is not None:
            category.sort_order = sort_order
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新Lut分类失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """删除Lut分类"""
    try:
        category = LutCategory.query.get_or_404(category_id)
        
        # 检查是否有文件使用该分类
        from app.models.lut_file import LutFile
        file_count = LutFile.query.filter_by(category_id=category_id).count()
        if file_count > 0:
            return jsonify({'code': 400, 'message': f'该分类下还有 {file_count} 个文件，无法删除'}), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除Lut分类失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

