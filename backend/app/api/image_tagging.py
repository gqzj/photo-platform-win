from flask import Blueprint, request, jsonify, send_file, current_app
from app.database import db
from app.models.image import Image
from app.models.image_recycle import ImageRecycle
from app.utils.config_manager import get_local_image_dir
import json
import os
import traceback
from datetime import datetime

bp = Blueprint('image_tagging', __name__)

@bp.route('', methods=['GET'])
def get_image_list():
    """获取图片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', type=str)
        
        query = Image.query.filter_by(status='active')
        
        if keyword:
            query = query.filter(Image.keyword.like(f'%{keyword}%'))
        
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

@bp.route('/<int:image_id>', methods=['GET'])
def get_image_detail(image_id):
    """获取图片详情"""
    try:
        image = Image.query.get_or_404(image_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': image.to_dict()
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:image_id>/tags', methods=['PUT'])
def update_image_tags(image_id):
    """更新图片标签"""
    try:
        image = Image.query.get_or_404(image_id)
        data = request.get_json()
        tags = data.get('tags', [])
        
        # 将标签列表转换为JSON字符串
        image.hash_tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '标签更新成功',
            'data': image.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/batch-tags', methods=['POST'])
def batch_update_tags():
    """批量更新标签"""
    try:
        data = request.get_json()
        image_ids = data.get('ids', [])
        tags = data.get('tags', [])
        
        tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
        
        for image_id in image_ids:
            image = Image.query.get(image_id)
            if image:
                image.hash_tags_json = tags_json
                db.session.add(image)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '批量更新标签成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/file/<int:image_id>', methods=['GET'])
def get_image_file(image_id):
    """获取图片文件URL（返回JSON格式）"""
    try:
        image = Image.query.get_or_404(image_id)
        
        # 优先使用本地存储路径
        if image.storage_path:
            # 规范化路径（统一使用正斜杠）
            relative_path = image.storage_path.replace('\\', '/')
            
            # 获取配置的基础目录（绝对路径）
            storage_base = get_local_image_dir()
            
            # 移除相对路径开头的 ./ 或 .\
            relative_path = relative_path.lstrip('./').lstrip('.\\')
            
            # 拼接完整路径
            file_path = os.path.join(storage_base, relative_path)
            
            # 规范化路径（处理..和.，统一分隔符）
            file_path = os.path.normpath(file_path)
            
            # 检查文件是否存在
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # 文件存在，返回可以直接访问的URL
                image_url = f'/api/images/file/{image_id}/content'
                current_app.logger.info(f"返回图片URL: {image_url}, 文件路径: {file_path}")
                return jsonify({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'url': image_url
                    }
                })
            else:
                current_app.logger.warning(f"图片文件不存在: {file_path}, 原始storage_path: {image.storage_path}")
        
        # 如果有原始URL，返回原始URL
        if image.original_url:
            current_app.logger.info(f"返回原始URL: {image.original_url}")
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'url': image.original_url
                }
            })
        
        # 文件不存在
        current_app.logger.error(f"图片文件不存在，ID: {image_id}, storage_path: {image.storage_path}")
        return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
        
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取图片文件失败，ID: {image_id}, 错误: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/file/<int:image_id>/content', methods=['GET'])
def get_image_file_content(image_id):
    """获取图片文件内容（实际文件流）"""
    try:
        image = Image.query.get_or_404(image_id)
        
        if not image.storage_path:
            return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
        
        # 规范化路径
        # 规范化路径（统一使用正斜杠）
        relative_path = image.storage_path.replace('\\', '/')
        
        # 获取配置的基础目录（绝对路径）
        storage_base = get_local_image_dir()
        
        # 移除相对路径开头的 ./ 或 .\
        relative_path = relative_path.lstrip('./').lstrip('.\\')
        
        # 拼接完整路径
        file_path = os.path.join(storage_base, relative_path)
        
        # 规范化路径（处理..和.，统一分隔符）
        file_path = os.path.normpath(file_path)
        
        # 检查文件是否存在
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path)
        else:
            return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取图片文件内容失败，ID: {image_id}, 错误: {error_detail}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:image_id>/recycle', methods=['POST'])
def recycle_image(image_id):
    """将图片移动到回收站（人工删除）"""
    try:
        image = Image.query.get_or_404(image_id)
        
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
            'cleaning_reason': '人工删除',  # 清洗原因：人工删除
            'recycled_at': datetime.now()
        }
        
        recycle_obj = ImageRecycle(**recycle_data)
        db.session.add(recycle_obj)
        
        # 删除语义搜索索引中的记录（如果存在）
        from app.models.semantic_search import SemanticSearchImage
        semantic_search_image = SemanticSearchImage.query.filter_by(image_id=image_id).first()
        if semantic_search_image:
            # 从FAISS索引中删除
            try:
                from app.services.semantic_search_service import get_semantic_search_service
                service = get_semantic_search_service()
                service.initialize()
                service.delete_image_vector(image_id)
            except Exception as e:
                current_app.logger.warning(f"从语义搜索索引中删除图片失败: {str(e)}")
            
            # 从数据库删除语义搜索记录
            db.session.delete(semantic_search_image)
        
        # 删除所有相关的样本集图片关联记录（避免外键约束错误）
        from app.models.sample_set import SampleSetImage
        SampleSetImage.query.filter_by(image_id=image_id).delete()
        
        # 删除该图片的美学评分记录（避免外键约束错误）
        from app.models.aesthetic_score import AestheticScore
        AestheticScore.query.filter_by(image_id=image_id).delete()
        
        # 删除特征风格子风格图片关联记录（避免外键约束错误）
        from app.models.feature_style_definition import FeatureStyleSubStyleImage
        FeatureStyleSubStyleImage.query.filter_by(image_id=image_id).delete()
        
        # 删除风格图片关联记录（避免外键约束错误）
        from app.models.style import StyleImage
        StyleImage.query.filter_by(image_id=image_id).delete()
        
        # 刷新session以确保删除操作被记录
        db.session.flush()
        
        # 从images表删除
        db.session.delete(image)
        
        db.session.commit()
        
        current_app.logger.info(f"图片已移动到回收站: image_id={image_id}, reason=人工删除")
        
        return jsonify({
            'code': 200,
            'message': '图片已移动到回收站',
            'data': {
                'image_id': image_id
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"移动图片到回收站失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
