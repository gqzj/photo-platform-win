# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app, send_file
from app.database import db
from app.models.sample_set import SampleSet, SampleSetFeature, SampleSetImage
from app.models.feature import Feature
from app.models.image import Image
import traceback
import json
import os
import threading
from datetime import datetime

bp = Blueprint('sample_set', __name__)

@bp.route('', methods=['GET'])
def get_sample_set_list():
    """获取样本集列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        status = request.args.get('status', type=str)
        
        query = SampleSet.query
        
        if keyword:
            query = query.filter(SampleSet.name.like(f'%{keyword}%'))
        
        if status:
            query = query.filter(SampleSet.status == status)
        
        total = query.count()
        sample_sets = query.order_by(SampleSet.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [sample_set.to_dict() for sample_set in sample_sets],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取样本集列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>', methods=['GET'])
def get_sample_set_detail(sample_set_id):
    """获取样本集详情"""
    try:
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': sample_set.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取样本集详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_sample_set():
    """创建样本集"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '样本集名称不能为空'}), 400
        
        # 创建样本集
        sample_set = SampleSet(
            name=data['name'],
            description=data.get('description'),
            status=data.get('status', 'active')
        )
        
        db.session.add(sample_set)
        db.session.flush()  # 获取ID
        
        # 处理特征配置
        features = data.get('features', [])
        if features:
            for feature_data in features:
                feature_id = feature_data.get('feature_id')
                feature_name = feature_data.get('feature_name', '')
                value_range = feature_data.get('value_range')
                value_type = feature_data.get('value_type', 'enum')
                
                if feature_id:
                    # 获取特征信息
                    feature = Feature.query.get(feature_id)
                    if feature:
                        feature_name = feature.name
                    
                    # 处理value_range
                    value_range_json = None
                    if value_range is not None:
                        if value_type == 'enum':
                            # 枚举类型：确保是数组
                            if isinstance(value_range, list):
                                value_range_json = json.dumps(value_range, ensure_ascii=False)
                            elif isinstance(value_range, str):
                                # 如果是字符串，尝试解析
                                try:
                                    parsed = json.loads(value_range)
                                    value_range_json = json.dumps(parsed if isinstance(parsed, list) else [parsed], ensure_ascii=False)
                                except:
                                    value_range_json = json.dumps([value_range], ensure_ascii=False)
                        elif value_type == 'range':
                            # 范围类型：确保是对象
                            if isinstance(value_range, dict):
                                value_range_json = json.dumps(value_range, ensure_ascii=False)
                            elif isinstance(value_range, str):
                                try:
                                    parsed = json.loads(value_range)
                                    value_range_json = json.dumps(parsed if isinstance(parsed, dict) else {}, ensure_ascii=False)
                                except:
                                    value_range_json = None
                        # any类型不需要value_range
                    
                    sample_set_feature = SampleSetFeature(
                        sample_set_id=sample_set.id,
                        feature_id=feature_id,
                        feature_name=feature_name,
                        value_range=value_range_json,
                        value_type=value_type
                    )
                    db.session.add(sample_set_feature)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': sample_set.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建样本集失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>', methods=['PUT'])
def update_sample_set(sample_set_id):
    """更新样本集"""
    try:
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '样本集名称不能为空'}), 400
        
        # 更新字段
        sample_set.name = data['name']
        sample_set.description = data.get('description')
        sample_set.status = data.get('status', sample_set.status)
        sample_set.updated_at = datetime.now()
        
        # 更新特征配置（先删除旧的，再添加新的）
        SampleSetFeature.query.filter_by(sample_set_id=sample_set_id).delete()
        
        features = data.get('features', [])
        if features:
            for feature_data in features:
                feature_id = feature_data.get('feature_id')
                feature_name = feature_data.get('feature_name', '')
                value_range = feature_data.get('value_range')
                value_type = feature_data.get('value_type', 'enum')
                
                if feature_id:
                    # 获取特征信息
                    feature = Feature.query.get(feature_id)
                    if feature:
                        feature_name = feature.name
                    
                    # 处理value_range
                    value_range_json = None
                    if value_range is not None:
                        if value_type == 'enum':
                            # 枚举类型：确保是数组
                            if isinstance(value_range, list):
                                value_range_json = json.dumps(value_range, ensure_ascii=False)
                            elif isinstance(value_range, str):
                                # 如果是字符串，尝试解析
                                try:
                                    parsed = json.loads(value_range)
                                    value_range_json = json.dumps(parsed if isinstance(parsed, list) else [parsed], ensure_ascii=False)
                                except:
                                    value_range_json = json.dumps([value_range], ensure_ascii=False)
                        elif value_type == 'range':
                            # 范围类型：确保是对象
                            if isinstance(value_range, dict):
                                value_range_json = json.dumps(value_range, ensure_ascii=False)
                            elif isinstance(value_range, str):
                                try:
                                    parsed = json.loads(value_range)
                                    value_range_json = json.dumps(parsed if isinstance(parsed, dict) else {}, ensure_ascii=False)
                                except:
                                    value_range_json = None
                        # any类型不需要value_range
                    
                    sample_set_feature = SampleSetFeature(
                        sample_set_id=sample_set_id,
                        feature_id=feature_id,
                        feature_name=feature_name,
                        value_range=value_range_json,
                        value_type=value_type
                    )
                    db.session.add(sample_set_feature)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': sample_set.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新样本集失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>', methods=['DELETE'])
def delete_sample_set(sample_set_id):
    """删除样本集"""
    try:
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        db.session.delete(sample_set)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除样本集失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch', methods=['DELETE'])
def batch_delete_sample_sets():
    """批量删除样本集"""
    try:
        data = request.get_json()
        sample_set_ids = data.get('ids', [])
        
        if not sample_set_ids:
            return jsonify({'code': 400, 'message': '请选择要删除的样本集'}), 400
        
        SampleSet.query.filter(SampleSet.id.in_(sample_set_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功删除 {len(sample_set_ids)} 个样本集'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量删除样本集失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>/calculate', methods=['POST'])
def calculate_sample_set_data(sample_set_id):
    """计算样本集数据"""
    try:
        from app.services.sample_set_service import SampleSetService
        
        service = SampleSetService()
        result = service.calculate_sample_set_data(sample_set_id)
        
        if result['success']:
            return jsonify({
                'code': 200,
                'message': result['message'],
                'data': {
                    'matched_count': result.get('matched_count', 0)
                }
            })
        else:
            return jsonify({
                'code': 400,
                'message': result['message']
            }), 400
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"计算样本集数据失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>/refresh', methods=['POST'])
def refresh_sample_set(sample_set_id):
    """刷新样本集状态"""
    try:
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        
        # 刷新数据库对象
        db.session.refresh(sample_set)
        
        # 重新计算图片数量（从sample_set_images表统计）
        image_count = SampleSetImage.query.filter_by(sample_set_id=sample_set_id).count()
        sample_set.image_count = image_count
        
        # 检查打包文件是否存在
        if sample_set.package_status == 'packed' and sample_set.package_path:
            if not os.path.exists(sample_set.package_path):
                # 如果文件不存在，更新状态为未打包
                sample_set.package_status = 'unpacked'
                sample_set.package_path = None
                sample_set.packaged_at = None
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '刷新成功',
            'data': sample_set.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"刷新样本集状态失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>/images', methods=['GET'])
def get_sample_set_images(sample_set_id):
    """获取样本集中的图片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 24, type=int)
        keyword = request.args.get('keyword', type=str)
        
        # 验证样本集是否存在
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        
        # 通过 sample_set_images 关联查询 images
        query = db.session.query(Image).join(
            SampleSetImage,
            Image.id == SampleSetImage.image_id
        ).filter(
            SampleSetImage.sample_set_id == sample_set_id
        )
        
        if keyword:
            query = query.filter(
                db.or_(
                    Image.filename.like(f'%{keyword}%'),
                    Image.keyword.like(f'%{keyword}%')
                )
            )
        
        total = query.count()
        images = query.order_by(Image.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [img.to_dict() for img in images],
                'total': total,
                'page': page,
                'page_size': page_size,
                'sample_set': {
                    'id': sample_set.id,
                    'name': sample_set.name,
                    'description': sample_set.description,
                    'image_count': sample_set.image_count
                }
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取样本集图片列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>/feature-distribution', methods=['GET'])
def get_feature_distribution(sample_set_id):
    """获取样本集的特征分布"""
    try:
        from app.models.image_tagging_result import ImageTaggingResult
        from sqlalchemy import func
        
        # 验证样本集是否存在
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        
        # 获取样本集的特征配置
        features = SampleSetFeature.query.filter_by(sample_set_id=sample_set_id).all()
        if not features:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'distribution': []
                }
            })
        
        # 获取样本集中的所有图片ID
        sample_set_image_ids = db.session.query(SampleSetImage.image_id).filter_by(
            sample_set_id=sample_set_id
        ).subquery()
        
        # 获取最新的打标结果（按image_id和feature_id分组，取最新的updated_at）
        subquery = db.session.query(
            ImageTaggingResult.image_id,
            ImageTaggingResult.feature_id,
            func.max(ImageTaggingResult.updated_at).label('max_updated_at')
        ).filter(
            ImageTaggingResult.image_id.in_(db.session.query(sample_set_image_ids))
        ).group_by(
            ImageTaggingResult.image_id,
            ImageTaggingResult.feature_id
        ).subquery()
        
        # 获取最新的打标结果
        latest_results = db.session.query(ImageTaggingResult).join(
            subquery,
            db.and_(
                ImageTaggingResult.image_id == subquery.c.image_id,
                ImageTaggingResult.feature_id == subquery.c.feature_id,
                ImageTaggingResult.updated_at == subquery.c.max_updated_at
            )
        ).filter(
            ImageTaggingResult.feature_id.in_([f.feature_id for f in features])
        ).all()
        
        # 统计每个特征值的分布
        distribution = []
        for feature in features:
            feature_name = feature.feature_name
            feature_id = feature.feature_id
            
            # 统计该特征的所有值
            value_counts = {}
            for result in latest_results:
                if result.feature_id == feature_id and result.tagging_value:
                    value = result.tagging_value
                    value_counts[value] = value_counts.get(value, 0) + 1
            
            # 转换为列表格式
            value_list = [
                {
                    'value': value,
                    'count': count
                }
                for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
            ]
            
            distribution.append({
                'feature_id': feature_id,
                'feature_name': feature_name,
                'values': value_list,
                'total': sum(value_counts.values())
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'distribution': distribution
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取特征分布失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>/package', methods=['POST'])
def package_sample_set(sample_set_id):
    """打包样本集"""
    try:
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        
        # 检查是否正在打包
        if sample_set.package_status == 'packing':
            return jsonify({
                'code': 400,
                'message': '样本集正在打包中，请稍候'
            }), 400
        
        # 在后台线程中执行打包
        def do_package():
            """在后台线程中执行打包任务"""
            try:
                # 需要导入app来创建新的应用上下文
                from app import create_app
                app_instance = create_app()
                with app_instance.app_context():
                    from app.services.package_service import PackageService
                    service = PackageService()
                    result = service.package_sample_set(sample_set_id)
                    if result['success']:
                        current_app.logger.info(f"打包成功 {sample_set_id}: {result.get('package_path', '')}, 复制图片数: {result.get('copied_count', 0)}")
                    else:
                        current_app.logger.error(f"打包失败 {sample_set_id}: {result.get('message', '未知错误')}")
            except Exception as e:
                # 如果无法使用current_app，使用标准logging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"后台执行打包任务异常 {sample_set_id}: {str(e)}", exc_info=True)
        
        thread = threading.Thread(target=do_package)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'code': 200,
            'message': '打包任务已启动，请稍候查看打包状态'
        })
        
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动打包任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:sample_set_id>/download', methods=['GET'])
def download_sample_set_package(sample_set_id):
    """下载样本集压缩包"""
    try:
        sample_set = SampleSet.query.get_or_404(sample_set_id)
        
        if sample_set.package_status != 'packed':
            return jsonify({
                'code': 400,
                'message': '样本集尚未打包完成，无法下载'
            }), 400
        
        if not sample_set.package_path or not os.path.exists(sample_set.package_path):
            return jsonify({
                'code': 404,
                'message': '压缩包文件不存在'
            }), 404
        
        # 生成下载文件名
        zip_filename = os.path.basename(sample_set.package_path)
        
        return send_file(
            sample_set.package_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"下载压缩包失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

