# -*- coding: utf-8 -*-
"""
特征风格定义API
"""
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.feature_style_definition import FeatureStyleDefinition, FeatureStyleSubStyle, FeatureStyleSubStyleImage
from app.models.image import Image
from app.models.image_tagging_result_detail import ImageTaggingResultDetail
from app.models.feature import Feature
import traceback
import json
from itertools import product
from datetime import datetime
from sqlalchemy import and_

bp = Blueprint('feature_style_definition', __name__)

def _match_images_by_dimension_values(dimension_values_dict, feature_name_to_id):
    """
    根据维度值组合匹配图片
    
    Args:
        dimension_values_dict: 维度值组合字典，格式：{"特征名": "特征值"}
        feature_name_to_id: 特征名称到特征ID的映射
    
    Returns:
        匹配的图片ID列表
    """
    try:
        from flask import current_app
        
        # 构建查询条件：每个维度都需要匹配
        # 需要找到同时满足所有维度条件的图片（AND关系）
        
        # 方法：先查询每个条件的图片ID集合，然后取交集
        image_id_sets = []
        
        for feature_name, feature_value in dimension_values_dict.items():
            feature_id = feature_name_to_id.get(feature_name)
            if not feature_id:
                current_app.logger.warning(f"特征 {feature_name} 没有找到对应的特征ID")
                continue
            
            # 查询该特征和特征值匹配的图片
            matching_details = ImageTaggingResultDetail.query.filter(
                ImageTaggingResultDetail.feature_id == feature_id,
                ImageTaggingResultDetail.tagging_value == str(feature_value)
            ).all()
            
            image_ids = {detail.image_id for detail in matching_details}
            if image_ids:
                image_id_sets.append(image_ids)
                current_app.logger.debug(f"特征 {feature_name}={feature_value} 匹配到 {len(image_ids)} 张图片")
            else:
                current_app.logger.debug(f"特征 {feature_name}={feature_value} 没有匹配到图片")
        
        if not image_id_sets:
            return []
        
        # 取交集：所有条件都满足的图片
        matched_image_ids = set(image_id_sets[0])
        for image_id_set in image_id_sets[1:]:
            matched_image_ids = matched_image_ids & image_id_set
        
        if not matched_image_ids:
            return []
        
        # 过滤掉已删除的图片
        active_images = Image.query.filter(
            Image.id.in_(list(matched_image_ids)),
            Image.status == 'active'
        ).all()
        active_image_ids = [img.id for img in active_images]
        
        current_app.logger.info(f"维度值组合 {dimension_values_dict} 匹配到 {len(active_image_ids)} 张有效图片")
        
        return active_image_ids
        
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"匹配图片失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return []

@bp.route('', methods=['GET'])
def get_feature_style_definition_list():
    """获取特征风格定义列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        status = request.args.get('status', type=str)
        
        query = FeatureStyleDefinition.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    FeatureStyleDefinition.name.like(f'%{keyword}%'),
                    FeatureStyleDefinition.description.like(f'%{keyword}%')
                )
            )
        
        if status:
            query = query.filter(FeatureStyleDefinition.status == status)
        
        total = query.count()
        definitions = query.order_by(FeatureStyleDefinition.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [defn.to_dict() for defn in definitions],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征风格定义列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:definition_id>', methods=['GET'])
def get_feature_style_definition_detail(definition_id):
    """获取特征风格定义详情"""
    try:
        definition = FeatureStyleDefinition.query.get_or_404(definition_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': definition.to_dict(include_sub_styles=True)
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征风格定义详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_feature_style_definition():
    """创建特征风格定义"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '风格定义名称不能为空'}), 400
        
        # 检查名称是否已存在（使用锁机制避免并发问题）
        existing = FeatureStyleDefinition.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'code': 400, 'message': '风格定义名称已存在'}), 400
        
        # 验证维度数据
        dimensions = data.get('dimensions', [])
        if not dimensions or not isinstance(dimensions, list):
            return jsonify({'code': 400, 'message': '维度数据不能为空'}), 400
        
        # 验证并转换维度数据（从特征ID获取特征名称）
        from app.models.feature import Feature
        validated_dimensions = []
        for dim in dimensions:
            feature_id = dim.get('feature_id')
            if not feature_id:
                return jsonify({'code': 400, 'message': '维度必须选择特征'}), 400
            
            feature = Feature.query.get(feature_id)
            if not feature:
                return jsonify({'code': 400, 'message': f'特征ID {feature_id} 不存在'}), 400
            
            if not feature.enabled:
                return jsonify({'code': 400, 'message': f'特征 {feature.name} 已禁用，不能使用'}), 400
            
            if not dim.get('values') or not isinstance(dim['values'], list) or len(dim['values']) == 0:
                return jsonify({'code': 400, 'message': f'特征 {feature.name} 至少需要选择一个特征值'}), 400
            
            validated_dimensions.append({
                'dimension_name': feature.name,
                'values': dim['values']
            })
        
        # 创建特征风格定义
        try:
            definition = FeatureStyleDefinition(
                name=data['name'],
                description=data.get('description'),
                dimensions_json=json.dumps(validated_dimensions, ensure_ascii=False),
                status=data.get('status', 'active')
            )
            
            db.session.add(definition)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            # 检查是否是重复键错误
            if 'Duplicate entry' in str(db_error) or '1062' in str(db_error):
                return jsonify({'code': 400, 'message': '风格定义名称已存在，请使用其他名称'}), 400
            raise
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': definition.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建特征风格定义失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:definition_id>', methods=['PUT'])
def update_feature_style_definition(definition_id):
    """更新特征风格定义"""
    try:
        definition = FeatureStyleDefinition.query.get_or_404(definition_id)
        data = request.get_json()
        
        # 如果更新名称，检查是否与其他定义冲突
        if 'name' in data and data['name'] != definition.name:
            existing = FeatureStyleDefinition.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'code': 400, 'message': '风格定义名称已存在'}), 400
            definition.name = data['name']
        
        # 更新其他字段
        if 'description' in data:
            definition.description = data['description']
        
        if 'status' in data:
            definition.status = data['status']
        
        # 更新维度数据
        if 'dimensions' in data:
            dimensions = data['dimensions']
            if not isinstance(dimensions, list):
                return jsonify({'code': 400, 'message': '维度数据格式错误'}), 400
            
            # 验证并转换维度数据（从特征ID获取特征名称）
            from app.models.feature import Feature
            validated_dimensions = []
            for dim in dimensions:
                feature_id = dim.get('feature_id')
                if not feature_id:
                    return jsonify({'code': 400, 'message': '维度必须选择特征'}), 400
                
                feature = Feature.query.get(feature_id)
                if not feature:
                    return jsonify({'code': 400, 'message': f'特征ID {feature_id} 不存在'}), 400
                
                if not feature.enabled:
                    return jsonify({'code': 400, 'message': f'特征 {feature.name} 已禁用，不能使用'}), 400
                
                if not dim.get('values') or not isinstance(dim['values'], list) or len(dim['values']) == 0:
                    return jsonify({'code': 400, 'message': f'特征 {feature.name} 至少需要选择一个特征值'}), 400
                
                validated_dimensions.append({
                    'dimension_name': feature.name,
                    'values': dim['values']
                })
            
            definition.dimensions_json = json.dumps(validated_dimensions, ensure_ascii=False)
        
        definition.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': definition.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新特征风格定义失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:definition_id>', methods=['DELETE'])
def delete_feature_style_definition(definition_id):
    """删除特征风格定义"""
    try:
        definition = FeatureStyleDefinition.query.get_or_404(definition_id)
        db.session.delete(definition)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除特征风格定义失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:definition_id>/generate-sub-styles', methods=['POST'])
def generate_sub_styles(definition_id):
    """生成子风格（笛卡尔积排列组合）"""
    try:
        definition = FeatureStyleDefinition.query.get_or_404(definition_id)
        
        # 解析维度数据
        dimensions_data = []
        if definition.dimensions_json:
            try:
                dimensions_data = json.loads(definition.dimensions_json) if isinstance(definition.dimensions_json, str) else definition.dimensions_json
            except:
                return jsonify({'code': 400, 'message': '维度数据格式错误'}), 400
        
        if not dimensions_data:
            return jsonify({'code': 400, 'message': '没有定义维度'}), 400
        
        # 删除现有的子风格
        existing_sub_styles = FeatureStyleSubStyle.query.filter_by(feature_style_definition_id=definition_id).all()
        for sub_style in existing_sub_styles:
            db.session.delete(sub_style)
        db.session.flush()
        
        # 获取特征ID映射（维度名称 -> 特征ID）
        feature_name_to_id = {}
        for dim in dimensions_data:
            feature_name = dim['dimension_name']
            feature = Feature.query.filter_by(name=feature_name, enabled=True).first()
            if feature:
                feature_name_to_id[feature_name] = feature.id
            else:
                current_app.logger.warning(f"特征 {feature_name} 不存在或已禁用")
        
        # 生成笛卡尔积
        dimension_names = [dim['dimension_name'] for dim in dimensions_data]
        dimension_values = [dim['values'] for dim in dimensions_data]
        
        # 计算组合总数（不实际生成，只计算数量）
        total_combinations = 1
        for values in dimension_values:
            total_combinations *= len(values)
        
        # 检查组合数量是否超过限制
        MAX_COMBINATIONS = 10000
        if total_combinations > MAX_COMBINATIONS:
            return jsonify({
                'code': 400,
                'message': f'组合数量过多（{total_combinations} 个），超过最大限制（{MAX_COMBINATIONS} 个）。请减少维度或特征值的数量。'
            }), 400
        
        # 计算所有组合（在内存中）
        combinations = list(product(*dimension_values))
        current_app.logger.info(f"计算得到 {len(combinations)} 个维度组合")
        
        # 先在内存中匹配所有组合的图片，只保存有图片的组合
        valid_combinations = []  # 存储有图片的组合及其匹配的图片ID列表
        
        for idx, combination in enumerate(combinations):
            # 构建维度值组合字典
            dimension_values_dict = {dimension_names[i]: combination[i] for i in range(len(dimension_names))}
            
            # 在内存中匹配图片（不访问数据库创建记录）
            matched_image_ids = _match_images_by_dimension_values(
                dimension_values_dict, 
                feature_name_to_id
            )
            
            # 只保存有图片的组合
            if matched_image_ids:
                # 生成子风格名称（格式：维度1值1-维度2值2-...）
                sub_style_name = '-'.join([f"{dimension_names[i]}{combination[i]}" for i in range(len(combination))])
                
                valid_combinations.append({
                    'name': sub_style_name,
                    'dimension_values_dict': dimension_values_dict,
                    'image_ids': matched_image_ids,
                    'image_count': len(matched_image_ids)
                })
                
                if (idx + 1) % 10 == 0:
                    current_app.logger.info(f"已处理 {idx + 1}/{len(combinations)} 个组合，找到 {len(valid_combinations)} 个有效组合")
        
        current_app.logger.info(f"共找到 {len(valid_combinations)} 个有图片的组合，将保存到数据库")
        
        # 批量创建子风格和图片关联（只保存有图片的组合）
        created_count = 0
        total_matched_images = 0
        
        for combo_data in valid_combinations:
            # 检查是否已存在（理论上不应该存在，因为已经删除了）
            existing = FeatureStyleSubStyle.query.filter_by(
                feature_style_definition_id=definition_id,
                name=combo_data['name']
            ).first()
            
            if not existing:
                # 创建子风格
                sub_style = FeatureStyleSubStyle(
                    feature_style_definition_id=definition_id,
                    name=combo_data['name'],
                    dimension_values_json=json.dumps(combo_data['dimension_values_dict'], ensure_ascii=False),
                    description=f"维度组合：{combo_data['name']}",
                    image_count=combo_data['image_count']
                )
                db.session.add(sub_style)
                db.session.flush()  # 获取sub_style.id
                
                # 批量添加图片关联
                for image_id in combo_data['image_ids']:
                    sub_style_image = FeatureStyleSubStyleImage(
                        sub_style_id=sub_style.id,
                        image_id=image_id
                    )
                    db.session.add(sub_style_image)
                
                created_count += 1
                total_matched_images += combo_data['image_count']
        
        db.session.commit()
        
        current_app.logger.info(f"为特征风格定义 {definition.name} 生成了 {created_count} 个子风格（共 {len(combinations)} 个组合，{len(combinations) - created_count} 个无图片组合已跳过），共匹配 {total_matched_images} 张图片")
        
        return jsonify({
            'code': 200,
            'message': '子风格生成成功',
            'data': {
                'definition_id': definition_id,
                'created_count': created_count,
                'total_combinations': len(combinations),
                'skipped_count': len(combinations) - created_count,
                'total_matched_images': total_matched_images
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"生成子风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:definition_id>/sub-styles', methods=['GET'])
def get_sub_styles(definition_id):
    """获取子风格列表"""
    try:
        definition = FeatureStyleDefinition.query.get_or_404(definition_id)
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        query = FeatureStyleSubStyle.query.filter_by(feature_style_definition_id=definition_id)
        
        if keyword:
            query = query.filter(FeatureStyleSubStyle.name.like(f'%{keyword}%'))
        
        total = query.count()
        # 按照图片数量降序排序，图片数量相同的按ID降序排序
        sub_styles = query.order_by(FeatureStyleSubStyle.image_count.desc(), FeatureStyleSubStyle.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'definition_id': definition_id,
                'definition_name': definition.name,
                'list': [sub_style.to_dict() for sub_style in sub_styles],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取子风格列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/sub-styles/<int:sub_style_id>/images', methods=['GET'])
def get_sub_style_images(sub_style_id):
    """获取子风格图片列表"""
    try:
        sub_style = FeatureStyleSubStyle.query.get_or_404(sub_style_id)
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        query = FeatureStyleSubStyleImage.query.filter_by(sub_style_id=sub_style_id)
        
        total = query.count()
        sub_style_images = query.order_by(FeatureStyleSubStyleImage.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'sub_style_id': sub_style_id,
                'sub_style_name': sub_style.name,
                'list': [img.to_dict() for img in sub_style_images],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取子风格图片列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/sub-styles/<int:sub_style_id>/images', methods=['POST'])
def add_images_to_sub_style(sub_style_id):
    """添加图片到子风格"""
    try:
        sub_style = FeatureStyleSubStyle.query.get_or_404(sub_style_id)
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({'code': 400, 'message': '图片ID列表不能为空'}), 400
        
        # 检查图片是否存在
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        existing_image_ids = {img.id for img in images}
        missing_ids = set(image_ids) - existing_image_ids
        if missing_ids:
            return jsonify({'code': 400, 'message': f'图片不存在: {missing_ids}'}), 400
        
        # 检查是否已添加
        existing_sub_style_images = FeatureStyleSubStyleImage.query.filter(
            FeatureStyleSubStyleImage.sub_style_id == sub_style_id,
            FeatureStyleSubStyleImage.image_id.in_(image_ids)
        ).all()
        existing_added_ids = {si.image_id for si in existing_sub_style_images}
        
        # 添加新图片
        added_count = 0
        for image_id in image_ids:
            if image_id not in existing_added_ids:
                sub_style_image = FeatureStyleSubStyleImage(
                    sub_style_id=sub_style_id,
                    image_id=image_id
                )
                db.session.add(sub_style_image)
                added_count += 1
        
        # 更新子风格的图片数量
        sub_style.image_count = FeatureStyleSubStyleImage.query.filter_by(sub_style_id=sub_style_id).count()
        sub_style.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'added_count': added_count,
                'skipped_count': len(existing_added_ids),
                'image_count': sub_style.image_count
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"添加图片到子风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/sub-styles/<int:sub_style_id>/images/<int:image_id>', methods=['DELETE'])
def remove_image_from_sub_style(sub_style_id, image_id):
    """从子风格中删除图片"""
    try:
        sub_style = FeatureStyleSubStyle.query.get_or_404(sub_style_id)
        
        sub_style_image = FeatureStyleSubStyleImage.query.filter_by(
            sub_style_id=sub_style_id,
            image_id=image_id
        ).first()
        
        if not sub_style_image:
            return jsonify({'code': 404, 'message': '图片不在该子风格中'}), 404
        
        db.session.delete(sub_style_image)
        
        # 更新子风格的图片数量
        sub_style.image_count = FeatureStyleSubStyleImage.query.filter_by(sub_style_id=sub_style_id).count()
        sub_style.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': {
                'image_count': sub_style.image_count
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"从子风格中删除图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
