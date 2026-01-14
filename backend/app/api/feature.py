from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.feature import Feature
import traceback
import json

bp = Blueprint('feature', __name__)

@bp.route('', methods=['GET'])
def get_feature_list():
    """获取特征列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        category = request.args.get('category', type=str)
        status = request.args.get('status', type=str)
        
        query = Feature.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    Feature.name.like(f'%{keyword}%'),
                    Feature.description.like(f'%{keyword}%')
                )
            )
        
        if category:
            query = query.filter(Feature.category == category)
        
        if status:
            # 兼容前端传入的 'active'/'inactive'，转换为 enabled 布尔值
            if status == 'active':
                query = query.filter(Feature.enabled == True)
            elif status == 'inactive':
                query = query.filter(Feature.enabled == False)
        
        total = query.count()
        features = query.order_by(Feature.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [feature.to_dict() for feature in features],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:feature_id>', methods=['GET'])
def get_feature_detail(feature_id):
    """获取特征详情"""
    try:
        feature = Feature.query.get_or_404(feature_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': feature.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_feature():
    """创建特征"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '特征名称不能为空'}), 400
        
        # 检查名称是否已存在
        existing = Feature.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'code': 400, 'message': '特征名称已存在'}), 400
        
        # 创建特征
        # 处理 status/enabled 字段兼容
        enabled = True
        if 'status' in data:
            enabled = data['status'] == 'active'
        elif 'enabled' in data:
            enabled = bool(data['enabled'])
        
        feature = Feature(
            name=data['name'],
            description=data.get('description'),
            category=data.get('category'),
            color=data.get('color'),
            auto_tagging=data.get('auto_tagging', False),
            values_json=data.get('values_json'),
            enabled=enabled
        )
        
        db.session.add(feature)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': feature.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建特征失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:feature_id>', methods=['PUT'])
def update_feature(feature_id):
    """更新特征"""
    try:
        feature = Feature.query.get_or_404(feature_id)
        data = request.get_json()
        
        # 如果更新名称，检查是否与其他特征冲突
        if 'name' in data and data['name'] != feature.name:
            existing = Feature.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'code': 400, 'message': '特征名称已存在'}), 400
            feature.name = data['name']
        
        # 更新其他字段
        if 'description' in data:
            feature.description = data['description']
        if 'category' in data:
            feature.category = data['category']
        if 'color' in data:
            feature.color = data['color']
        if 'auto_tagging' in data:
            feature.auto_tagging = bool(data['auto_tagging'])
        if 'values_json' in data:
            feature.values_json = data['values_json']
        # 处理 status/enabled 字段兼容
        if 'status' in data:
            feature.enabled = data['status'] == 'active'
        elif 'enabled' in data:
            feature.enabled = bool(data['enabled'])
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': feature.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新特征失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:feature_id>', methods=['DELETE'])
def delete_feature(feature_id):
    """删除特征"""
    try:
        feature = Feature.query.get_or_404(feature_id)
        
        # 先清空与特征组的关联关系（避免级联删除时的期望更新行数问题）
        from app.models.feature_group import FeatureGroupFeature
        # 使用 SQL 直接删除，避免 SQLAlchemy 的关联更新问题
        FeatureGroupFeature.query.filter_by(feature_id=feature_id).delete(synchronize_session=False)
        
        # 刷新session以确保删除操作被记录
        db.session.flush()
        
        # 从 session 中移除 feature 对象，避免关联更新
        db.session.expunge(feature)
        
        # 重新查询并删除（确保是干净的状态）
        feature = Feature.query.get(feature_id)
        if feature:
            db.session.delete(feature)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除特征失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch', methods=['DELETE'])
def batch_delete_features():
    """批量删除特征"""
    try:
        data = request.get_json()
        feature_ids = data.get('ids', [])
        
        if not feature_ids:
            return jsonify({'code': 400, 'message': '请选择要删除的特征'}), 400
        
        # 先查询存在的特征，然后逐个删除（避免期望更新行数的问题）
        from app.models.feature_group import FeatureGroupFeature
        features = Feature.query.filter(Feature.id.in_(feature_ids)).all()
        deleted_count = 0
        
        for feature in features:
            # 先清空与特征组的关联关系（使用 SQL 直接删除，避免 SQLAlchemy 的关联更新问题）
            FeatureGroupFeature.query.filter_by(feature_id=feature.id).delete(synchronize_session=False)
            deleted_count += 1
        
        # 刷新session以确保删除操作被记录
        db.session.flush()
        
        # 从 session 中移除所有 feature 对象，避免关联更新
        for feature in features:
            db.session.expunge(feature)
        
        # 重新查询并删除（确保是干净的状态）
        features_to_delete = Feature.query.filter(Feature.id.in_(feature_ids)).all()
        for feature in features_to_delete:
            db.session.delete(feature)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功删除 {deleted_count} 个特征'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量删除特征失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        categories = db.session.query(Feature.category).distinct().filter(Feature.category.isnot(None)).all()
        category_list = [cat[0] for cat in categories if cat[0]]
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': category_list
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取分类列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

