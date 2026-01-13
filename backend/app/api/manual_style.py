# -*- coding: utf-8 -*-
"""
手工风格管理API
"""
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.style import Style, StyleImage
from app.models.image import Image
from app.models.lut_file import LutFile
from app.models.lut_category import LutCategory
from app.services.semantic_search_service import get_semantic_search_service
from app.services.lut_extraction_service import LutExtractionService
from app.utils.config_manager import get_local_image_dir
from app.api.lut_file import get_lut_storage_dir
import traceback
import os
import tempfile
import hashlib
import shutil
from datetime import datetime

bp = Blueprint('manual_style', __name__)

@bp.route('', methods=['GET'])
def get_manual_style_list():
    """获取手工风格列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        status = request.args.get('status', type=str)
        
        query = Style.query.filter(Style.is_manual == True)
        
        if keyword:
            query = query.filter(
                Style.name.like(f'%{keyword}%')
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
                'page': page,
                'page_size': page_size,
                'total': total
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取手工风格列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_manual_style():
    """创建手工风格"""
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'code': 400, 'message': '风格名称不能为空'}), 400
        
        # 检查名称是否已存在
        existing = Style.query.filter_by(name=name).first()
        if existing:
            return jsonify({'code': 400, 'message': '风格名称已存在'}), 400
        
        # 创建风格
        style = Style(
            name=name,
            description=description,
            is_manual=True,
            status='active',
            image_count=0
        )
        db.session.add(style)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': style.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建手工风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>', methods=['DELETE'])
def delete_manual_style(style_id):
    """删除手工风格"""
    try:
        style = Style.query.filter_by(id=style_id, is_manual=True).first()
        if not style:
            return jsonify({'code': 404, 'message': '风格不存在'}), 404
        
        db.session.delete(style)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除手工风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>', methods=['GET'])
def get_manual_style(style_id):
    """获取手工风格详情"""
    try:
        style = Style.query.filter_by(id=style_id, is_manual=True).first()
        if not style:
            return jsonify({'code': 404, 'message': '风格不存在'}), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': style.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取手工风格详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/images', methods=['GET'])
def get_style_images(style_id):
    """获取风格的图片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        style = Style.query.filter_by(id=style_id, is_manual=True).first()
        if not style:
            return jsonify({'code': 404, 'message': '风格不存在'}), 404
        
        query = StyleImage.query.filter_by(style_id=style_id)
        total = query.count()
        style_images = query.order_by(StyleImage.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [si.to_dict() for si in style_images],
                'page': page,
                'page_size': page_size,
                'total': total,
                'style': style.to_dict()
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取风格图片列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/images/search', methods=['POST'])
def search_images_for_style(style_id):
    """使用语义搜索为风格查找图片（支持文本和图片搜索）"""
    try:
        style = Style.query.filter_by(id=style_id, is_manual=True).first()
        if not style:
            return jsonify({'code': 404, 'message': '风格不存在'}), 404
        
        # 使用语义搜索服务
        service = get_semantic_search_service()
        service.initialize()
        
        # 判断是文本搜索还是图片搜索
        # 优先检查是否有文件上传
        if 'image' in request.files:
            # 图片搜索
            file = request.files['image']
            top_k = request.form.get('top_k', 20, type=int)
            
            if file.filename == '':
                return jsonify({'code': 400, 'message': '请上传有效的图片文件'}), 400
            
            # 保存临时文件
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"search_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(temp_path)
            
            try:
                # 执行图片搜索
                results = service.search_by_image(temp_path, top_k=top_k)
                search_type = 'image'
                query_value = file.filename
            finally:
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            # 文本搜索
            # 根据Content-Type决定如何获取数据
            content_type = request.content_type or ''
            
            if 'application/json' in content_type:
                # JSON请求
                data = request.get_json() or {}
            else:
                # 表单数据或其他格式
                data = request.form.to_dict() or {}
                # 如果form为空，尝试从args获取（GET参数）
                if not data:
                    data = request.args.to_dict() or {}
            
            query_text = data.get('query', '').strip()
            top_k = data.get('top_k', 20)
            
            if not query_text:
                return jsonify({'code': 400, 'message': '查询文本不能为空'}), 400
            
            # 执行文本搜索
            results = service.search_by_text(query_text, top_k=top_k)
            search_type = 'text'
            query_value = query_text
        
        # 获取已添加到风格的图片ID
        existing_image_ids = set(
            db.session.query(StyleImage.image_id)
            .filter_by(style_id=style_id)
            .all()
        )
        existing_image_ids = {row[0] for row in existing_image_ids}
        
        # 获取图片详情并标记是否已添加
        image_ids = [r['image_id'] for r in results]
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        image_map = {img.id: img for img in images}
        
        search_results = []
        for result in results:
            image_id = result['image_id']
            if image_id in image_map:
                image = image_map[image_id]
                search_results.append({
                    'image_id': image_id,
                    'score': result['score'],
                    'distance': result['distance'],
                    'image': image.to_dict(),
                    'already_added': image_id in existing_image_ids
                })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'search_type': search_type,
                'query': query_value,
                'results': search_results,
                'total': len(search_results)
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"语义搜索失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/images', methods=['POST'])
def add_images_to_style(style_id):
    """添加图片到风格"""
    try:
        data = request.get_json() or {}
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({'code': 400, 'message': '图片ID列表不能为空'}), 400
        
        style = Style.query.filter_by(id=style_id, is_manual=True).first()
        if not style:
            return jsonify({'code': 404, 'message': '风格不存在'}), 404
        
        # 检查图片是否存在
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        existing_image_ids = {img.id for img in images}
        missing_ids = set(image_ids) - existing_image_ids
        if missing_ids:
            return jsonify({'code': 400, 'message': f'图片不存在: {missing_ids}'}), 400
        
        # 检查是否已添加
        existing_style_images = StyleImage.query.filter(
            StyleImage.style_id == style_id,
            StyleImage.image_id.in_(image_ids)
        ).all()
        existing_added_ids = {si.image_id for si in existing_style_images}
        
        # 添加新图片
        added_count = 0
        for image_id in image_ids:
            if image_id not in existing_added_ids:
                style_image = StyleImage(
                    style_id=style_id,
                    image_id=image_id
                )
                db.session.add(style_image)
                added_count += 1
        
        # 更新风格的图片数量
        style.image_count = StyleImage.query.filter_by(style_id=style_id).count()
        style.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'added_count': added_count,
                'skipped_count': len(existing_added_ids),
                'image_count': style.image_count
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"添加图片到风格失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/images/<int:image_id>', methods=['DELETE'])
def remove_image_from_style(style_id, image_id):
    """从风格中删除图片"""
    try:
        style = Style.query.filter_by(id=style_id, is_manual=True).first()
        if not style:
            return jsonify({'code': 404, 'message': '风格不存在'}), 404
        
        style_image = StyleImage.query.filter_by(style_id=style_id, image_id=image_id).first()
        if not style_image:
            return jsonify({'code': 404, 'message': '图片不在该风格中'}), 404
        
        db.session.delete(style_image)
        
        # 更新风格的图片数量
        style.image_count = StyleImage.query.filter_by(style_id=style_id).count()
        style.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'image_count': style.image_count
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"从风格中删除图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:style_id>/extract-lut', methods=['POST'])
def extract_lut(style_id):
    """提取风格的LUT（方法2：从图片集合中提取）"""
    try:
        style = Style.query.filter_by(id=style_id, is_manual=True).first()
        if not style:
            return jsonify({'code': 404, 'message': '风格不存在'}), 404
        
        # 检查是否有图片
        style_images = StyleImage.query.filter_by(style_id=style_id).all()
        if not style_images:
            return jsonify({'code': 400, 'message': '风格中没有图片，无法提取LUT'}), 400
        
        # 获取所有图片的路径
        image_paths = []
        storage_base = get_local_image_dir()
        
        for style_image in style_images:
            image = style_image.image
            if not image or not image.storage_path:
                continue
            
            # 构建完整文件路径
            relative_path = image.storage_path.replace('\\', '/').lstrip('./').lstrip('.\\')
            file_path = os.path.join(storage_base, relative_path)
            file_path = os.path.normpath(file_path)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                image_paths.append(file_path)
        
        if not image_paths:
            return jsonify({'code': 400, 'message': '没有找到有效的图片文件'}), 400
        
        current_app.logger.info(f"开始为风格 {style.name} 提取LUT，共 {len(image_paths)} 张图片")
        
        # 创建LUT提取服务
        extraction_service = LutExtractionService()
        
        # 创建临时LUT文件
        temp_dir = tempfile.gettempdir()
        temp_lut_path = os.path.join(temp_dir, f"style_{style_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cube")
        
        # 提取LUT
        success, error_msg = extraction_service.extract_lut_from_images(image_paths, temp_lut_path)
        
        if not success:
            return jsonify({'code': 500, 'message': f'LUT提取失败: {error_msg}'}), 500
        
        # 确保"手工风格定义"分类存在
        category_name = '手工风格定义'
        category = LutCategory.query.filter_by(name=category_name).first()
        if not category:
            category = LutCategory(
                name=category_name,
                description='从手工风格定义中提取的LUT文件',
                sort_order=0
            )
            db.session.add(category)
            db.session.flush()  # 获取ID
            current_app.logger.info(f"创建新分类: {category_name}, ID: {category.id}")
        
        # 确保分类名称存在
        if not category.name:
            category.name = category_name
            db.session.flush()
        
        current_app.logger.info(f"使用分类: {category.name}, ID: {category.id}")
        
        # 准备上传LUT文件
        lut_storage_dir = get_lut_storage_dir()
        category_dir = os.path.join(lut_storage_dir, str(category.id))
        os.makedirs(category_dir, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = f"{style.name}_{timestamp}.cube"
        unique_filename = f"{timestamp}_{os.urandom(4).hex()}_{original_filename}"
        
        # 保存LUT文件（使用shutil.move支持跨磁盘移动）
        final_lut_path = os.path.join(category_dir, unique_filename)
        shutil.move(temp_lut_path, final_lut_path)
        
        # 计算文件大小和哈希值
        file_size = os.path.getsize(final_lut_path)
        hash_md5 = hashlib.md5()
        with open(final_lut_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        file_hash = hash_md5.hexdigest()
        
        # 检查是否已存在相同哈希的文件
        existing_hash = LutFile.query.filter_by(file_hash=file_hash).first()
        if existing_hash:
            # 删除刚创建的文件
            os.remove(final_lut_path)
            return jsonify({
                'code': 200,
                'message': 'LUT文件已存在（相同哈希值）',
                'data': {
                    'lut_file_id': existing_hash.id,
                    'lut_file_name': existing_hash.original_filename,
                    'style_id': style_id,
                    'style_name': style.name
                }
            })
        
        # 检查是否已存在相同的category_id和original_filename组合
        existing_unique = LutFile.query.filter_by(
            category_id=category.id,
            original_filename=original_filename
        ).first()
        if existing_unique:
            # 删除刚创建的文件
            os.remove(final_lut_path)
            return jsonify({
                'code': 200,
                'message': '该类别下已存在同名文件',
                'data': {
                    'lut_file_id': existing_unique.id,
                    'lut_file_name': existing_unique.original_filename,
                    'style_id': style_id,
                    'style_name': style.name
                }
            })
        
        # 创建数据库记录
        relative_path = os.path.join(str(category.id), unique_filename).replace('\\', '/')
        lut_file = LutFile(
            category_id=category.id,
            filename=unique_filename,
            original_filename=original_filename,
            storage_path=relative_path,
            file_size=file_size,
            file_hash=file_hash,
            description=f"从手工风格 '{style.name}' 提取的LUT文件，包含 {len(image_paths)} 张图片"
        )
        
        db.session.add(lut_file)
        db.session.commit()
        
        # 刷新对象以获取最新数据
        db.session.refresh(lut_file)
        db.session.refresh(category)
        
        current_app.logger.info(f"LUT提取成功，文件ID: {lut_file.id}, 文件名: {original_filename}, 分类: {category.name}")
        
        # 验证文件是否存在
        if not os.path.exists(final_lut_path):
            current_app.logger.error(f"LUT文件不存在: {final_lut_path}")
            return jsonify({'code': 500, 'message': 'LUT文件保存失败，文件不存在'}), 500
        
        return jsonify({
            'code': 200,
            'message': 'LUT提取成功',
            'data': {
                'lut_file_id': lut_file.id,
                'lut_file_name': lut_file.original_filename,
                'lut_file_path': lut_file.storage_path,
                'style_id': style_id,
                'style_name': style.name,
                'image_count': len(image_paths),
                'category_id': category.id,
                'category_name': category.name or '手工风格定义'  # 确保有默认值
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"提取LUT失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
