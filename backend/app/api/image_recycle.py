# -*- coding: utf-8 -*-
"""图片回收站API"""
from flask import Blueprint, request, jsonify, send_file, current_app
from app.database import db
from app.models.image_recycle import ImageRecycle
from app.models.image import Image
from app.utils.config_manager import get_local_image_dir
import os
import traceback
from sqlalchemy import text

bp = Blueprint('image_recycle', __name__)

@bp.route('', methods=['GET'])
def get_recycle_list():
    """获取回收站图片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', type=str)
        cleaning_task_id = request.args.get('cleaning_task_id', type=int)
        cleaning_reason = request.args.get('cleaning_reason', type=str)
        
        query = ImageRecycle.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    ImageRecycle.filename.like(f'%{keyword}%'),
                    ImageRecycle.keyword.like(f'%{keyword}%')
                )
            )
        
        if cleaning_task_id:
            query = query.filter(ImageRecycle.cleaning_task_id == cleaning_task_id)
        
        if cleaning_reason:
            query = query.filter(ImageRecycle.cleaning_reason.like(f'%{cleaning_reason}%'))
        
        total = query.count()
        images = query.order_by(ImageRecycle.recycled_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
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
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取回收站图片列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>', methods=['GET'])
def get_recycle_detail(image_id):
    """获取回收站图片详情"""
    try:
        image = ImageRecycle.query.get_or_404(image_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': image.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取回收站图片详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/file/<int:image_id>/content', methods=['GET'])
def get_recycle_image_content(image_id):
    """获取回收站图片文件内容（实际文件流）"""
    try:
        image = ImageRecycle.query.get_or_404(image_id)
        
        if not image.storage_path:
            current_app.logger.warning(f"回收站图片文件不存在 (ID: {image_id}): storage_path为空")
            return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
        
        # 规范化路径
        file_path = image.storage_path.replace('\\', '/')
        
        # 获取配置的基础目录（绝对路径）
        storage_base = get_local_image_dir()
        
        # 移除相对路径开头的 ./ 或 .\
        file_path = file_path.lstrip('./').lstrip('.\\')
        
        # 拼接完整路径
        file_path = os.path.join(storage_base, file_path)
        
        # 规范化路径（处理..和.，统一分隔符）
        file_path = os.path.normpath(file_path)
        
        # 检查文件是否存在
        if os.path.exists(file_path) and os.path.isfile(file_path):
            current_app.logger.info(f"返回回收站图片文件内容: {file_path}")
            # 尝试根据文件扩展名猜测mimetype
            mimetype = None
            if '.' in file_path:
                ext = file_path.rsplit('.', 1)[1].lower()
                if ext == 'jpg' or ext == 'jpeg':
                    mimetype = 'image/jpeg'
                elif ext == 'png':
                    mimetype = 'image/png'
                elif ext == 'gif':
                    mimetype = 'image/gif'
            return send_file(file_path, mimetype=mimetype, as_attachment=False)
        else:
            current_app.logger.warning(f"回收站图片文件不存在: {file_path}, 原始storage_path: {image.storage_path}")
            return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取回收站图片文件内容失败，ID: {image_id}, 错误: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>/restore', methods=['POST'])
def restore_image(image_id):
    """还原单张图片到images表"""
    try:
        recycle_image = ImageRecycle.query.get_or_404(image_id)
        
        # 准备图片数据
        image_data = {
            'filename': recycle_image.filename,
            'storage_path': recycle_image.storage_path,
            'original_url': recycle_image.original_url,
            'status': 'active',
            'created_at': recycle_image.created_at,
            'storage_mode': recycle_image.storage_mode,
            'source_site': recycle_image.source_site,
            'keyword': recycle_image.keyword,
            'hash_tags_json': recycle_image.hash_tags_json,
            'visit_url': recycle_image.visit_url,
            'image_hash': recycle_image.image_hash,
            'width': recycle_image.width,
            'height': recycle_image.height,
            'format': recycle_image.format
        }
        
        # 如果original_image_id存在，尝试使用该id
        if recycle_image.original_image_id:
            # 检查images表中是否已存在该id
            existing_image = Image.query.get(recycle_image.original_image_id)
            if existing_image:
                # 如果存在，更新记录
                for key, value in image_data.items():
                    setattr(existing_image, key, value)
                restored_image = existing_image
                current_app.logger.info(f"更新已存在的图片记录: id={recycle_image.original_image_id}")
            else:
                # 如果不存在，创建新记录并指定id
                # 使用SQL直接插入指定id
                try:
                    db.session.execute(
                        text("""
                            INSERT INTO images (id, filename, storage_path, original_url, status, created_at, 
                                                storage_mode, source_site, keyword, hash_tags_json, visit_url, 
                                                image_hash, width, height, format)
                            VALUES (:id, :filename, :storage_path, :original_url, :status, :created_at,
                                    :storage_mode, :source_site, :keyword, :hash_tags_json, :visit_url,
                                    :image_hash, :width, :height, :format)
                        """),
                        {
                            'id': recycle_image.original_image_id,
                            'filename': image_data['filename'],
                            'storage_path': image_data['storage_path'],
                            'original_url': image_data['original_url'],
                            'status': image_data['status'],
                            'created_at': image_data['created_at'],
                            'storage_mode': image_data['storage_mode'],
                            'source_site': image_data['source_site'],
                            'keyword': image_data['keyword'],
                            'hash_tags_json': image_data['hash_tags_json'],
                            'visit_url': image_data['visit_url'],
                            'image_hash': image_data['image_hash'],
                            'width': image_data['width'],
                            'height': image_data['height'],
                            'format': image_data['format']
                        }
                    )
                    db.session.commit()
                    # 重新查询获取对象
                    restored_image = Image.query.get(recycle_image.original_image_id)
                    current_app.logger.info(f"创建新图片记录并指定id: id={recycle_image.original_image_id}")
                except Exception as e:
                    db.session.rollback()
                    # 如果插入失败（可能是id冲突），创建新记录让数据库自动分配id
                    current_app.logger.warning(f"无法使用original_image_id {recycle_image.original_image_id}，创建新记录: {e}")
                    restored_image = Image(**image_data)
                    db.session.add(restored_image)
                    db.session.commit()
                    db.session.refresh(restored_image)
        else:
            # 如果没有original_image_id，创建新记录
            restored_image = Image(**image_data)
            db.session.add(restored_image)
            db.session.commit()
            db.session.refresh(restored_image)
        
        # 从回收站删除
        db.session.delete(recycle_image)
        db.session.commit()
        
        current_app.logger.info(f"图片已还原: recycle_id={image_id}, image_id={restored_image.id}")
        
        return jsonify({
            'code': 200,
            'message': '图片还原成功',
            'data': {
                'restored_image_id': restored_image.id,
                'original_image_id': recycle_image.original_image_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"还原图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch/restore', methods=['POST'])
def batch_restore_images():
    """批量还原图片到images表"""
    try:
        data = request.get_json()
        image_ids = data.get('ids', [])
        
        if not image_ids:
            return jsonify({'code': 400, 'message': '请选择要还原的图片'}), 400
        
        recycle_images = ImageRecycle.query.filter(ImageRecycle.id.in_(image_ids)).all()
        
        if not recycle_images:
            return jsonify({'code': 404, 'message': '未找到要还原的图片'}), 404
        
        restored_count = 0
        failed_count = 0
        errors = []
        
        for recycle_image in recycle_images:
            try:
                # 准备图片数据
                image_data = {
                    'filename': recycle_image.filename,
                    'storage_path': recycle_image.storage_path,
                    'original_url': recycle_image.original_url,
                    'status': 'active',
                    'created_at': recycle_image.created_at,
                    'storage_mode': recycle_image.storage_mode,
                    'source_site': recycle_image.source_site,
                    'keyword': recycle_image.keyword,
                    'hash_tags_json': recycle_image.hash_tags_json,
                    'visit_url': recycle_image.visit_url,
                    'image_hash': recycle_image.image_hash,
                    'width': recycle_image.width,
                    'height': recycle_image.height,
                    'format': recycle_image.format
                }
                
                # 如果original_image_id存在，尝试使用该id
                if recycle_image.original_image_id:
                    existing_image = Image.query.get(recycle_image.original_image_id)
                    if existing_image:
                        # 更新已存在的记录
                        for key, value in image_data.items():
                            setattr(existing_image, key, value)
                        restored_image = existing_image
                    else:
                        # 创建新记录并指定id
                        try:
                            db.session.execute(
                                text("""
                                    INSERT INTO images (id, filename, storage_path, original_url, status, created_at, 
                                                        storage_mode, source_site, keyword, hash_tags_json, visit_url, 
                                                        image_hash, width, height, format)
                                    VALUES (:id, :filename, :storage_path, :original_url, :status, :created_at,
                                            :storage_mode, :source_site, :keyword, :hash_tags_json, :visit_url,
                                            :image_hash, :width, :height, :format)
                                """),
                                {
                                    'id': recycle_image.original_image_id,
                                    'filename': image_data['filename'],
                                    'storage_path': image_data['storage_path'],
                                    'original_url': image_data['original_url'],
                                    'status': image_data['status'],
                                    'created_at': image_data['created_at'],
                                    'storage_mode': image_data['storage_mode'],
                                    'source_site': image_data['source_site'],
                                    'keyword': image_data['keyword'],
                                    'hash_tags_json': image_data['hash_tags_json'],
                                    'visit_url': image_data['visit_url'],
                                    'image_hash': image_data['image_hash'],
                                    'width': image_data['width'],
                                    'height': image_data['height'],
                                    'format': image_data['format']
                                }
                            )
                            db.session.commit()
                            restored_image = Image.query.get(recycle_image.original_image_id)
                        except Exception as e:
                            db.session.rollback()
                            # 如果插入失败，创建新记录
                            restored_image = Image(**image_data)
                            db.session.add(restored_image)
                            db.session.commit()
                            db.session.refresh(restored_image)
                else:
                    # 创建新记录
                    restored_image = Image(**image_data)
                    db.session.add(restored_image)
                    db.session.commit()
                    db.session.refresh(restored_image)
                
                # 从回收站删除
                db.session.delete(recycle_image)
                db.session.commit()
                
                restored_count += 1
                
            except Exception as e:
                db.session.rollback()
                error_msg = f"还原图片失败 (recycle_id={recycle_image.id}): {str(e)}"
                errors.append(error_msg)
                current_app.logger.error(error_msg, exc_info=True)
                failed_count += 1
                continue
        
        return jsonify({
            'code': 200,
            'message': f'批量还原完成：成功 {restored_count} 张，失败 {failed_count} 张',
            'data': {
                'restored_count': restored_count,
                'failed_count': failed_count,
                'errors': errors
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量还原图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

