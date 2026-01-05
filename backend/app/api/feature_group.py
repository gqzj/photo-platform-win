from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.feature_group import FeatureGroup, FeatureGroupFeature
from app.models.feature import Feature
import traceback

bp = Blueprint('feature_group', __name__)

@bp.route('', methods=['GET'])
def get_feature_group_list():
    """获取特征组列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        status = request.args.get('status', type=str)
        
        query = FeatureGroup.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    FeatureGroup.name.like(f'%{keyword}%'),
                    FeatureGroup.description.like(f'%{keyword}%')
                )
            )
        
        if status:
            # 兼容前端传入的 'active'/'inactive'，转换为 enabled 布尔值
            if status == 'active':
                query = query.filter(FeatureGroup.enabled == True)
            elif status == 'inactive':
                query = query.filter(FeatureGroup.enabled == False)
        
        total = query.count()
        feature_groups = query.order_by(FeatureGroup.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [group.to_dict() for group in feature_groups],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征组列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/all', methods=['GET'])
def get_all_feature_groups():
    """获取所有启用的特征组（用于下拉选择）"""
    try:
        feature_groups = FeatureGroup.query.filter_by(enabled=True).order_by(FeatureGroup.id.desc()).all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [group.to_dict(include_features=False) for group in feature_groups]
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取所有特征组失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:group_id>', methods=['GET'])
def get_feature_group_detail(group_id):
    """获取特征组详情"""
    try:
        feature_group = FeatureGroup.query.get_or_404(group_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': feature_group.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征组详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_feature_group():
    """创建特征组"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '特征组名称不能为空'}), 400
        
        # 检查名称是否已存在
        existing = FeatureGroup.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'code': 400, 'message': '特征组名称已存在'}), 400
        
        # 创建特征组
        enabled = True
        if 'status' in data:
            enabled = data['status'] == 'active'
        elif 'enabled' in data:
            enabled = bool(data['enabled'])
        
        feature_group = FeatureGroup(
            name=data['name'],
            description=data.get('description'),
            enabled=enabled
        )
        
        db.session.add(feature_group)
        db.session.flush()  # 获取ID
        
        # 添加特征关联
        feature_ids = data.get('feature_ids', [])
        if feature_ids:
            for feature_id in feature_ids:
                feature = Feature.query.get(feature_id)
                if feature:
                    feature_group.features.append(feature)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': feature_group.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建特征组失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:group_id>', methods=['PUT'])
def update_feature_group(group_id):
    """更新特征组"""
    try:
        feature_group = FeatureGroup.query.get_or_404(group_id)
        data = request.get_json()
        
        # 如果更新名称，检查是否与其他特征组冲突
        if 'name' in data and data['name'] != feature_group.name:
            existing = FeatureGroup.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'code': 400, 'message': '特征组名称已存在'}), 400
            feature_group.name = data['name']
        
        # 更新其他字段
        if 'description' in data:
            feature_group.description = data['description']
        
        # 处理 status/enabled 字段兼容
        if 'status' in data:
            feature_group.enabled = data['status'] == 'active'
        elif 'enabled' in data:
            feature_group.enabled = bool(data['enabled'])
        
        # 更新特征关联
        if 'feature_ids' in data:
            # 清空现有关联
            FeatureGroupFeature.query.filter_by(feature_group_id=group_id).delete()
            # 添加新关联
            feature_ids = data.get('feature_ids', [])
            for feature_id in feature_ids:
                feature = Feature.query.get(feature_id)
                if feature:
                    feature_group.features.append(feature)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': feature_group.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新特征组失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:group_id>', methods=['DELETE'])
def delete_feature_group(group_id):
    """删除特征组"""
    try:
        feature_group = FeatureGroup.query.get_or_404(group_id)
        db.session.delete(feature_group)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除特征组失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch', methods=['DELETE'])
def batch_delete_feature_groups():
    """批量删除特征组"""
    try:
        data = request.get_json()
        group_ids = data.get('ids', [])
        
        if not group_ids:
            return jsonify({'code': 400, 'message': '请选择要删除的特征组'}), 400
        
        deleted_count = FeatureGroup.query.filter(FeatureGroup.id.in_(group_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功删除 {deleted_count} 个特征组'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量删除特征组失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

