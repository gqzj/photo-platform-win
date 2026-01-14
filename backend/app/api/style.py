# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.style import Style, StyleImage, StyleFeatureProfile
from app.models.sample_set import SampleSet, SampleSetImage, SampleSetFeature
from app.models.image import Image
from app.models.image_recycle import ImageRecycle
from app.models.image_tagging_result_detail import ImageTaggingResultDetail
from app.models.feature import Feature
from app.models.image_tagging_result import ImageTaggingResult
from app.models.aesthetic_score import AestheticScore
from app.utils.config_manager import get_local_image_dir
from sqlalchemy import func, or_ as sql_or, update
import traceback
import json
import os
import requests
import threading
from datetime import datetime

bp = Blueprint('style', __name__)

@bp.route('', methods=['GET'])
def get_style_list():
    """获取风格列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        status = request.args.get('status', type=str)
        
        query = Style.query
        
        if keyword:
            query = query.filter(
                sql_or(
                    Style.name.like(f'%{keyword}%'),
                    Style.description.like(f'%{keyword}%')
                )
            )
        
        if status:
            query = query.filter(Style.status == status)
        
        total = query.count()
        styles = query.order_by(Style.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [style.to_dict() for style in styles],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取风格列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>', methods=['GET'])
def get_style_detail(style_id):
    """获取风格详情"""
    try:
        style = Style.query.get_or_404(style_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': style.to_dict(include_profiles=True)
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取风格详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_style():
    """创建风格"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '风格名称不能为空'}), 400
        
        # 检查名称是否已存在
        existing = Style.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'code': 400, 'message': '风格名称已存在'}), 400
        
        # 创建风格
        style = Style(
            name=data['name'],
            description=data.get('description'),
            sample_set_id=data.get('sample_set_id'),
            status=data.get('status', 'active')
        )
        
        db.session.add(style)
        db.session.flush()  # 获取ID
        
        # 如果关联了样本集，从样本集导入图片
        if data.get('sample_set_id'):
            sample_set = SampleSet.query.get(data['sample_set_id'])
            if sample_set:
                # 获取样本集的所有图片
                sample_set_images = SampleSetImage.query.filter_by(sample_set_id=data['sample_set_id']).all()
                style_images = []
                for ssi in sample_set_images:
                    style_image = StyleImage(
                        style_id=style.id,
                        image_id=ssi.image_id
                    )
                    style_images.append(style_image)
                
                if style_images:
                    db.session.bulk_save_objects(style_images)
                    style.image_count = len(style_images)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': style.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>', methods=['PUT'])
def update_style(style_id):
    """更新风格"""
    try:
        style = Style.query.get_or_404(style_id)
        data = request.get_json()
        
        # 如果更新名称，检查是否与其他风格冲突
        if 'name' in data and data['name'] != style.name:
            existing = Style.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'code': 400, 'message': '风格名称已存在'}), 400
            style.name = data['name']
        
        # 更新其他字段
        if 'description' in data:
            style.description = data['description']
        if 'sample_set_id' in data:
            style.sample_set_id = data['sample_set_id']
        if 'status' in data:
            style.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': style.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>', methods=['DELETE'])
def delete_style(style_id):
    """删除风格"""
    try:
        style = Style.query.get_or_404(style_id)
        db.session.delete(style)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/images', methods=['GET'])
def get_style_images(style_id):
    """获取风格的图片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 24, type=int)
        
        style = Style.query.get_or_404(style_id)
        
        query = StyleImage.query.filter_by(style_id=style_id)
        total = query.count()
        style_images = query.order_by(StyleImage.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        images = []
        for si in style_images:
            if si.image:
                image_dict = si.image.to_dict()
                # 查询该图片的美学评分（获取最新的评分）
                aesthetic_scores = AestheticScore.query.filter_by(
                    style_id=style_id,
                    image_id=si.image.id
                ).order_by(AestheticScore.created_at.desc()).all()
                
                # 构建美学评分信息
                aesthetic_scores_info = []
                for score in aesthetic_scores:
                    aesthetic_scores_info.append({
                        'evaluator_type': score.evaluator_type,
                        'score': float(score.score) if score.score is not None else None,
                        'created_at': score.created_at.strftime('%Y-%m-%d %H:%M:%S') if score.created_at else None
                    })
                
                image_dict['aesthetic_scores'] = aesthetic_scores_info
                images.append(image_dict)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': images,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取风格图片列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/images/<int:image_id>/recycle', methods=['POST'])
def recycle_style_image(style_id, image_id):
    """将风格中的图片移动到回收站"""
    try:
        style = Style.query.get_or_404(style_id)
        image = Image.query.get_or_404(image_id)
        
        # 检查图片是否属于该风格
        style_image = StyleImage.query.filter_by(style_id=style_id, image_id=image_id).first()
        if not style_image:
            return jsonify({'code': 400, 'message': '该图片不属于此风格'}), 400
        
        # 移动到回收站
        recycle_data = {
            'original_image_id': image.id,
            'filename': image.filename,
            'storage_path': image.storage_path,
            'original_url': image.original_url,
            'status': 'recycled',
            'created_at': image.created_at,
            'storage_mode': image.storage_mode,
            'source_site': image.source_site,
            'keyword': image.keyword,
            'hash_tags_json': image.hash_tags_json,
            'visit_url': image.visit_url,
            'image_hash': image.image_hash,
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'cleaning_reason': 'style_crop',  # 回收原因：风格裁剪
            'recycled_at': datetime.now()
        }
        
        recycle_obj = ImageRecycle(**recycle_data)
        db.session.add(recycle_obj)
        
        # 从风格图片表中删除
        db.session.delete(style_image)
        
        # 删除所有相关的样本集图片关联记录（避免外键约束错误）
        SampleSetImage.query.filter_by(image_id=image_id).delete()
        
        # 删除该图片的美学评分记录（避免外键约束错误）
        AestheticScore.query.filter_by(image_id=image_id).delete()
        
        # 删除特征风格子风格图片关联记录（避免外键约束错误）
        from app.models.feature_style_definition import FeatureStyleSubStyleImage
        FeatureStyleSubStyleImage.query.filter_by(image_id=image_id).delete()
        
        # 删除图片的打标结果（可选，如果需要保留历史记录可以注释掉）
        # ImageTaggingResultDetail.query.filter_by(image_id=image_id).delete()
        # ImageTaggingResult.query.filter_by(image_id=image_id).delete()
        
        # 刷新session以确保删除操作被记录
        db.session.flush()
        
        # 从images表删除
        db.session.delete(image)
        
        # 更新风格的图片数量
        style.image_count = StyleImage.query.filter_by(style_id=style_id).count()
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '图片已移动到回收站',
            'data': {
                'style_id': style_id,
                'image_id': image_id
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"移动图片到回收站失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/calculate-feature-distribution', methods=['POST'])
def calculate_feature_distribution(style_id):
    """计算风格的特征分布"""
    try:
        style = Style.query.get_or_404(style_id)
        
        # 获取风格中的所有图片ID
        style_image_ids = db.session.query(StyleImage.image_id).filter_by(
            style_id=style_id
        ).subquery()
        
        # 如果风格关联了样本集，只计算样本集中配置的特征
        if style.sample_set_id:
            sample_set_features = SampleSetFeature.query.filter_by(sample_set_id=style.sample_set_id).all()
            if sample_set_features:
                # 只使用样本集中配置的特征ID
                feature_ids = [sf.feature_id for sf in sample_set_features]
                features = Feature.query.filter(
                    Feature.id.in_(feature_ids),
                    Feature.enabled == True
                ).all()
            else:
                # 样本集没有配置特征，返回空结果
                features = []
        else:
            # 没有关联样本集，使用所有启用的特征
            features = Feature.query.filter_by(enabled=True).all()
        
        # 清空旧的特征画像
        StyleFeatureProfile.query.filter_by(style_id=style_id).delete()
        
        # 计算每个特征分布
        profiles = []
        for feature in features:
            # 从明细表查询该特征在该风格图片中的打标结果
            tagging_details = ImageTaggingResultDetail.query.filter(
                ImageTaggingResultDetail.image_id.in_(db.session.query(style_image_ids)),
                ImageTaggingResultDetail.feature_id == feature.id
            ).all()
            
            # 统计每个特征值的数量
            value_counts = {}
            for detail in tagging_details:
                if detail.tagging_value:
                    value = detail.tagging_value
                    value_counts[value] = value_counts.get(value, 0) + 1
            
            # 计算总数
            total_count = sum(value_counts.values())
            
            # 转换为列表格式并排序，同时计算百分比
            distribution_list = []
            for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = round((count / total_count * 100), 2) if total_count > 0 else 0.0
                distribution_list.append({
                    'value': value,
                    'count': count,
                    'percentage': percentage
                })
            
            # 创建特征画像记录
            profile = StyleFeatureProfile(
                style_id=style_id,
                feature_id=feature.id,
                feature_name=feature.name,
                distribution_json=json.dumps(distribution_list, ensure_ascii=False) if distribution_list else None,
                is_selected=False  # 默认不选中
            )
            profiles.append(profile)
        
        # 批量插入
        if profiles:
            db.session.bulk_save_objects(profiles)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '特征分布计算完成',
            'data': {
                'style_id': style_id,
                'profile_count': len(profiles)
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"计算特征分布失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/feature-profiles', methods=['GET'])
def get_feature_profiles(style_id):
    """获取风格的特征画像列表"""
    try:
        style = Style.query.get_or_404(style_id)
        
        # 如果风格关联了样本集，只返回样本集中配置的特征
        if style.sample_set_id:
            sample_set_features = SampleSetFeature.query.filter_by(sample_set_id=style.sample_set_id).all()
            if sample_set_features:
                # 只返回样本集中配置的特征ID对应的画像
                feature_ids = [sf.feature_id for sf in sample_set_features]
                profiles = StyleFeatureProfile.query.filter(
                    StyleFeatureProfile.style_id == style_id,
                    StyleFeatureProfile.feature_id.in_(feature_ids)
                ).order_by(StyleFeatureProfile.feature_id).all()
            else:
                # 样本集没有配置特征，返回空列表
                profiles = []
        else:
            # 没有关联样本集，返回所有特征画像
            profiles = StyleFeatureProfile.query.filter_by(style_id=style_id).order_by(StyleFeatureProfile.feature_id).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [profile.to_dict() for profile in profiles]
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征画像列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/feature-profiles/<int:profile_id>', methods=['PUT'])
def update_feature_profile(style_id, profile_id):
    """更新特征画像（主要是is_selected字段）"""
    try:
        profile = StyleFeatureProfile.query.filter_by(
            style_id=style_id,
            id=profile_id
        ).first_or_404()
        
        data = request.get_json()
        
        if 'is_selected' in data:
            profile.is_selected = bool(data['is_selected'])
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': profile.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新特征画像失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/feature-profiles/batch-update', methods=['PUT'])
def batch_update_feature_profiles(style_id):
    """批量更新特征画像的选中状态"""
    try:
        data = request.get_json()
        selected_ids = data.get('selected_ids', [])
        
        # 先取消所有选中
        StyleFeatureProfile.query.filter_by(style_id=style_id).update({'is_selected': False})
        
        # 设置选中的特征
        if selected_ids:
            StyleFeatureProfile.query.filter(
                StyleFeatureProfile.style_id == style_id,
                StyleFeatureProfile.id.in_(selected_ids)
            ).update({'is_selected': True}, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '批量更新成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量更新特征画像失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/aesthetic-score', methods=['POST'])
def evaluate_aesthetic_score(style_id):
    """对风格中的图片进行美学评分"""
    try:
        style = Style.query.get_or_404(style_id)
        data = request.get_json()
        
        evaluator_type = data.get('evaluator_type', 'artimuse')  # artimuse 或 q_insight
        score_mode = data.get('score_mode', 'score_and_reason')  # score_only: 仅评分, score_and_reason: 评分和理由
        
        if evaluator_type not in ['artimuse', 'q_insight']:
            return jsonify({'code': 400, 'message': '不支持的评分器类型'}), 400
        
        if evaluator_type == 'q_insight':
            return jsonify({'code': 400, 'message': 'Q-Insight功能暂未实现'}), 400
        
        if score_mode not in ['score_only', 'score_and_reason']:
            return jsonify({'code': 400, 'message': '不支持的评分模式'}), 400
        
        # 获取风格中的所有图片
        style_images = StyleImage.query.filter_by(style_id=style_id).all()
        if not style_images:
            return jsonify({'code': 400, 'message': '该风格中没有图片'}), 400
        
        # 更新total_image_count
        style.total_image_count = len(style_images)
        db.session.commit()
        
        # 记录启动日志
        current_app.logger.info(f"启动风格 {style_id} 的美学评分任务，共 {len(style_images)} 张图片，评分器类型: {evaluator_type}，评分模式: {score_mode}")
        
        # 在后台线程中执行评分
        def evaluate_images():
            """在后台线程中执行评分"""
            import logging
            logger = logging.getLogger(__name__)
            try:
                from app import create_app
                app_instance = create_app()
                with app_instance.app_context():
                    # 重新查询风格和风格图片，确保数据是最新的
                    style_obj = Style.query.get(style_id)
                    if not style_obj:
                        logger.error(f"[后台线程] 风格 {style_id} 不存在")
                        return
                    
                    style_images_list = StyleImage.query.filter_by(style_id=style_id).all()
                    logger.info(f"[后台线程] 开始处理风格 {style_id} 的美学评分，共 {len(style_images_list)} 张图片，评分模式: {score_mode}")
                    
                    processed_count = 0
                    total_images = len(style_images_list)
                    
                    for idx, style_image in enumerate(style_images_list, 1):
                        if not style_image.image:
                            continue
                        
                        image = style_image.image
                        
                        # 验证image.id不为None
                        if not image.id:
                            logger.warning(f"[后台线程] 图片对象没有ID，跳过")
                            continue
                        
                        # 检查是否已经评分过
                        existing_score = AestheticScore.query.filter_by(
                            style_id=style_id,
                            image_id=image.id,
                            evaluator_type=evaluator_type
                        ).first()
                        
                        if existing_score:
                            # 跳过已评分的图片，但也要更新进度
                            processed_count += 1
                            # 更新处理进度
                            db.session.refresh(style_obj)
                            style_obj.processed_image_count = processed_count
                            db.session.commit()
                            logger.info(f"[后台线程] 图片 {image.id} 已评分过，跳过。进度: {processed_count}/{total_images}")
                            continue
                        
                        # 获取图片文件路径
                        if not image.storage_path:
                            continue
                        
                        relative_path = image.storage_path.replace('\\', '/')
                        storage_base = get_local_image_dir()
                        relative_path = relative_path.lstrip('./').lstrip('.\\')
                        file_path = os.path.join(storage_base, relative_path)
                        file_path = os.path.normpath(file_path)
                        
                        if not os.path.exists(file_path) or not os.path.isfile(file_path):
                            continue
                        
                        try:
                            # 记录开始评分日志
                            logger.info(f"[后台线程] 开始评分图片 {image.id} ({idx}/{total_images}): {file_path}")
                            
                            # 根据评分模式选择接口
                            if evaluator_type == 'artimuse':
                                if score_mode == 'score_only':
                                    api_url = 'http://localhost:5001/api/evaluate_score'
                                else:
                                    api_url = 'http://localhost:5001/api/evaluate'
                            else:
                                # Q-Insight接口后续实现
                                logger.error(f"[后台线程] Q-Insight评分器暂未实现")
                                continue
                            
                            # 调用ArtiMuse接口
                            with open(file_path, 'rb') as f:
                                files = {'image': f}
                                response = requests.post(
                                    api_url,
                                    files=files,
                                    timeout=300
                                )
                            
                            if response.status_code == 200:
                                try:
                                    result_data = response.json()
                                except json.JSONDecodeError as e:
                                    logger.error(f"[后台线程] 评分图片 {image.id} 失败: 无法解析JSON响应 - {response.text[:200]}")
                                    continue
                                
                                score = result_data.get('score') or result_data.get('aesthetic_score')
                                
                                if score is None:
                                    logger.warning(f"[后台线程] 评分图片 {image.id} 响应中没有score字段，响应数据: {result_data}")
                                    # 仍然保存响应数据，但score为None
                                else:
                                    logger.info(f"[后台线程] 图片 {image.id} 评分成功: {score}")
                                
                                # 验证image.id不为None
                                if not image.id:
                                    logger.error(f"[后台线程] 图片对象没有ID，无法保存评分结果")
                                    continue
                                
                                # 再次检查是否已经评分过（防止并发问题）
                                existing_score_check = AestheticScore.query.filter_by(
                                    style_id=style_id,
                                    image_id=image.id,
                                    evaluator_type=evaluator_type
                                ).first()
                                
                                if existing_score_check:
                                    # 验证existing_score_check的image_id不为None
                                    if existing_score_check.image_id is None:
                                        logger.warning(f"[后台线程] 发现image_id为None的记录（ID: {existing_score_check.id}），删除并重新创建")
                                        db.session.delete(existing_score_check)
                                        db.session.commit()
                                        # 创建新记录
                                        aesthetic_score = AestheticScore(
                                            style_id=style_id,
                                            image_id=image.id,
                                            evaluator_type=evaluator_type,
                                            score=score,
                                            details_json=json.dumps(result_data, ensure_ascii=False)
                                        )
                                        db.session.add(aesthetic_score)
                                    else:
                                        # 如果已存在且image_id有效，使用SQL直接更新，避免SQLAlchemy自动刷新问题
                                        try:
                                            # 刷新对象以确保获取最新状态
                                            db.session.refresh(existing_score_check)
                                            # 验证image_id不为None
                                            if existing_score_check.image_id is None:
                                                logger.warning(f"[后台线程] 记录ID {existing_score_check.id} 的image_id为None，删除并重新创建")
                                                db.session.delete(existing_score_check)
                                                db.session.flush()
                                                aesthetic_score = AestheticScore(
                                                    style_id=style_id,
                                                    image_id=image.id,
                                                    evaluator_type=evaluator_type,
                                                    score=score,
                                                    details_json=json.dumps(result_data, ensure_ascii=False)
                                                )
                                                db.session.add(aesthetic_score)
                                            else:
                                                # 使用SQL直接更新，明确指定所有字段
                                                db.session.execute(
                                                    update(AestheticScore)
                                                    .where(AestheticScore.id == existing_score_check.id)
                                                    .values(
                                                        score=score,
                                                        details_json=json.dumps(result_data, ensure_ascii=False),
                                                        image_id=image.id,  # 明确设置image_id
                                                        style_id=style_id   # 明确设置style_id
                                                    )
                                                )
                                                logger.info(f"[后台线程] 更新已存在的评分记录，图片 {image.id}")
                                        except Exception as e:
                                            logger.error(f"[后台线程] 更新评分记录失败: {str(e)}")
                                            # 如果更新失败，删除旧记录并创建新记录
                                            try:
                                                db.session.delete(existing_score_check)
                                                db.session.flush()
                                            except:
                                                pass
                                            aesthetic_score = AestheticScore(
                                                style_id=style_id,
                                                image_id=image.id,
                                                evaluator_type=evaluator_type,
                                                score=score,
                                                details_json=json.dumps(result_data, ensure_ascii=False)
                                            )
                                            db.session.add(aesthetic_score)
                                else:
                                    # 保存评分结果
                                    aesthetic_score = AestheticScore(
                                        style_id=style_id,
                                        image_id=image.id,
                                        evaluator_type=evaluator_type,
                                        score=score,
                                        details_json=json.dumps(result_data, ensure_ascii=False)
                                    )
                                    db.session.add(aesthetic_score)
                                
                                processed_count += 1
                                
                                # 每处理一张图片就更新进度
                                db.session.commit()
                                
                                # 重新查询style对象并更新进度
                                db.session.refresh(style_obj)
                                style_obj.processed_image_count = processed_count
                                db.session.commit()
                                
                                logger.info(f"[后台线程] 进度更新: {processed_count}/{total_images}")
                                
                                # 每处理10张图片提交一次评分结果（批量提交优化）
                                if processed_count % 10 == 0:
                                    logger.info(f"[后台线程] 已处理 {processed_count} 张图片，批量提交中...")
                            else:
                                logger.error(f"[后台线程] 评分图片 {image.id} 失败: HTTP {response.status_code} - {response.text[:200]}")
                                continue
                        except requests.exceptions.ConnectionError as e:
                            logger.error(f"[后台线程] 评分图片 {image.id} 失败: 无法连接到ArtiMuse服务 (http://localhost:5001)，请确保服务正在运行")
                            # 如果连接失败，停止后续处理
                            logger.error("[后台线程] ArtiMuse服务不可用，停止美学评分任务")
                            break
                        except requests.exceptions.Timeout as e:
                            logger.error(f"[后台线程] 评分图片 {image.id} 失败: 请求超时（超过300秒）")
                            continue
                        except Exception as e:
                            logger.error(f"[后台线程] 评分图片 {image.id} 失败: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                            continue
                    
                    # 最终提交
                    db.session.commit()
                    
                    # 最终更新处理进度
                    db.session.refresh(style_obj)
                    style_obj.processed_image_count = processed_count
                    db.session.commit()
                    
                    logger.info(f"[后台线程] 风格 {style_id} 美学评分完成，处理了 {processed_count}/{total_images} 张图片")
            except Exception as e:
                import traceback
                logger.error(f"[后台线程] 美学评分失败: {traceback.format_exc()}")
        
        # 启动后台线程
        thread = threading.Thread(target=evaluate_images, name=f"AestheticScore-{style_id}")
        thread.daemon = True
        thread.start()
        current_app.logger.info(f"美学评分后台线程已启动，线程ID: {thread.ident}, 线程名: {thread.name}")
        
        return jsonify({
            'code': 200,
            'message': '美学评分任务已启动',
            'data': {
                'style_id': style_id,
                'total_images': len(style_images)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动美学评分失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/aesthetic-scores', methods=['GET'])
def get_aesthetic_scores(style_id):
    """获取风格的美学评分列表"""
    try:
        style = Style.query.get_or_404(style_id)
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        evaluator_type = request.args.get('evaluator_type', type=str)
        
        query = AestheticScore.query.filter_by(style_id=style_id)
        
        if evaluator_type:
            query = query.filter_by(evaluator_type=evaluator_type)
        
        total = query.count()
        scores = query.order_by(AestheticScore.score.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [score.to_dict() for score in scores],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取美学评分列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

