# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app, send_file
from app.database import db
from app.models.sample_image import SampleImage
from app.models.lut_file import LutFile
from app.models.lut_category import LutCategory
from app.models.lut_application import LutApplication, LutAppliedImage
from app.models.lut_file_tag import LutFileTag
from app.models.sample_image_aesthetic_score import SampleImageAestheticScore, SampleImageAestheticScoreTask
from app.models.lut_applied_image_aesthetic_score import LutAppliedImageAestheticScore
from app.models.lut_applied_image_aesthetic_score_task import LutAppliedImageAestheticScoreTask
from app.models.lut_applied_image_preference import LutAppliedImagePreference
from app.utils.config_manager import get_local_image_dir
from app.services.lut_application_service import LutApplicationService
from werkzeug.utils import secure_filename
from PIL import Image as PILImage
import traceback
import os
import hashlib
import threading
import json
import requests
import re
from datetime import datetime

bp = Blueprint('sample_image', __name__)

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_sample_image_storage_dir():
    """获取样本图片存储目录"""
    base_dir = get_local_image_dir()
    sample_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'sample_images')
    os.makedirs(sample_dir, exist_ok=True)
    return sample_dir

def calculate_file_hash(file_path):
    """计算文件哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_image_info(file_path):
    """获取图片信息（宽度、高度、格式）"""
    try:
        with PILImage.open(file_path) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format.lower() if img.format else None
            }
    except Exception as e:
        current_app.logger.warning(f"获取图片信息失败: {file_path}, 错误: {e}")
        return {
            'width': None,
            'height': None,
            'format': None
        }

@bp.route('', methods=['GET'])
def get_sample_image_list():
    """获取样本图片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        query = SampleImage.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    SampleImage.filename.like(f'%{keyword}%'),
                    SampleImage.original_filename.like(f'%{keyword}%')
                )
            )
        
        total = query.count()
        images = query.order_by(SampleImage.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
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
        current_app.logger.error(f"获取样本图片列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>', methods=['GET'])
def get_sample_image(image_id):
    """获取样本图片详情"""
    try:
        sample_image = SampleImage.query.get_or_404(image_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': sample_image.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取样本图片详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def upload_sample_images():
    """批量上传样本图片"""
    try:
        if 'files' not in request.files:
            return jsonify({'code': 400, 'message': '没有上传文件'}), 400
        
        files = request.files.getlist('files')
        description = request.form.get('description', '')
        
        if not files or len(files) == 0:
            return jsonify({'code': 400, 'message': '文件列表为空'}), 400
        
        uploaded_images = []
        errors = []
        
        storage_dir = get_sample_image_storage_dir()
        
        for file in files:
            if file.filename == '':
                errors.append({'filename': '', 'error': '文件名为空'})
                continue
            
            if not allowed_file(file.filename):
                errors.append({'filename': file.filename, 'error': f'不支持的文件类型，仅支持: {", ".join(ALLOWED_EXTENSIONS)}'})
                continue
            
            try:
                original_filename = file.filename
                filename = secure_filename(original_filename)
                
                # 生成唯一文件名（避免重名）
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{os.urandom(4).hex()}_{filename}"
                
                file_path = os.path.join(storage_dir, unique_filename)
                relative_path = unique_filename
                
                # 保存文件
                file.save(file_path)
                
                # 计算文件大小和哈希值
                file_size = os.path.getsize(file_path)
                file_hash = calculate_file_hash(file_path)
                
                # 检查是否已存在相同哈希的文件
                existing = SampleImage.query.filter_by(file_hash=file_hash).first()
                if existing:
                    # 删除刚上传的文件
                    os.remove(file_path)
                    errors.append({'filename': original_filename, 'error': '文件已存在（相同哈希值）'})
                    continue
                
                # 获取图片信息
                image_info = get_image_info(file_path)
                
                # 创建数据库记录
                sample_image = SampleImage(
                    filename=unique_filename,
                    original_filename=original_filename,
                    storage_path=relative_path,
                    file_size=file_size,
                    file_hash=file_hash,
                    width=image_info['width'],
                    height=image_info['height'],
                    format=image_info['format'],
                    description=description
                )
                
                db.session.add(sample_image)
                uploaded_images.append(sample_image)
                
            except Exception as e:
                errors.append({'filename': file.filename, 'error': str(e)})
                current_app.logger.error(f"上传文件失败: {file.filename}, 错误: {traceback.format_exc()}")
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功上传 {len(uploaded_images)} 个文件',
            'data': {
                'uploaded': [img.to_dict() for img in uploaded_images],
                'errors': errors
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量上传样本图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>', methods=['PUT'])
def update_sample_image(image_id):
    """更新样本图片信息"""
    try:
        sample_image = SampleImage.query.get_or_404(image_id)
        data = request.get_json()
        
        description = data.get('description')
        
        if description is not None:
            sample_image.description = description
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': sample_image.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新样本图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>', methods=['DELETE'])
def delete_sample_image(image_id):
    """删除样本图片"""
    try:
        sample_image = SampleImage.query.get_or_404(image_id)
        
        # 删除物理文件
        storage_dir = get_sample_image_storage_dir()
        file_path = os.path.join(storage_dir, sample_image.storage_path)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                current_app.logger.warning(f"删除物理文件失败: {file_path}, 错误: {e}")
        
        # 删除数据库记录
        db.session.delete(sample_image)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除样本图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>/content', methods=['GET'])
def get_sample_image_content(image_id):
    """获取样本图片内容"""
    try:
        sample_image = SampleImage.query.get_or_404(image_id)
        
        storage_dir = get_sample_image_storage_dir()
        file_path = os.path.join(storage_dir, sample_image.storage_path)
        
        if not os.path.exists(file_path):
            return jsonify({'code': 404, 'message': '文件不存在'}), 404
        
        return send_file(file_path)
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取样本图片内容失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

def get_lut_applied_image_storage_dir():
    """获取LUT应用后的图片存储目录"""
    base_dir = get_local_image_dir()
    applied_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'lut_applied_images')
    os.makedirs(applied_dir, exist_ok=True)
    return applied_dir

def get_lut_storage_dir():
    """获取LUT文件存储目录"""
    base_dir = get_local_image_dir()
    lut_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'luts')
    return lut_dir

def apply_luts_to_image_task(application_id, sample_image_id):
    """后台任务：将LUT应用到图片"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app import create_app
        app_instance = create_app()
        with app_instance.app_context():
            try:
                logger.info(f"开始执行LUT应用任务: application_id={application_id}, sample_image_id={sample_image_id}")
                
                application = LutApplication.query.get(application_id)
                if not application:
                    logger.error(f"LUT应用任务不存在: {application_id}")
                    return
                
                sample_image = SampleImage.query.get(sample_image_id)
                if not sample_image:
                    logger.error(f"样本图片不存在: {sample_image_id}")
                    application.status = 'failed'
                    application.error_message = '样本图片不存在'
                    db.session.commit()
                    return
                
                # 获取所有LUT文件，预加载类别关联关系
                from sqlalchemy.orm import joinedload
                from app.models.lut_category import LutCategory
                lut_files = LutFile.query.options(
                    joinedload(LutFile.category)
                ).all()
                total_count = len(lut_files)
                logger.info(f"找到 {total_count} 个LUT文件")
                
                if total_count == 0:
                    logger.warning("没有找到LUT文件")
                    application.status = 'completed'
                    application.total_lut_count = 0
                    application.processed_lut_count = 0
                    application.finished_at = datetime.now()
                    db.session.commit()
                    return
                
                application.total_lut_count = total_count
                application.status = 'running'
                db.session.commit()
                logger.info(f"任务状态已更新为running，总LUT数: {total_count}")
                
                # 获取文件路径
                sample_storage_dir = get_sample_image_storage_dir()
                sample_image_path = os.path.join(sample_storage_dir, sample_image.storage_path)
                
                lut_storage_dir = get_lut_storage_dir()
                applied_storage_dir = get_lut_applied_image_storage_dir()
                
                lut_service = LutApplicationService()
                
                processed_count = 0
                success_count = 0
                skipped_count = 0  # 记录跳过的文件数量（已应用过的）
                failed_files = []  # 记录失败的文件信息
                logger.info(f"开始处理LUT文件，样本图片路径: {sample_image_path}")
                logger.info(f"LUT存储目录: {lut_storage_dir}")
                logger.info(f"应用后图片存储目录: {applied_storage_dir}")
                
                for lut_file in lut_files:
                    try:
                        logger.info(f"处理LUT文件 [{processed_count + 1}/{total_count}]: {lut_file.original_filename}")
                        
                        # 检查该LUT文件是否已经应用到该样本图片
                        existing_applied = LutAppliedImage.query.filter_by(
                            lut_file_id=lut_file.id,
                            sample_image_id=sample_image_id
                        ).first()
                        
                        if existing_applied:
                            logger.info(f"LUT文件 {lut_file.original_filename} (ID: {lut_file.id}) 已经应用到样本图片 {sample_image_id}，跳过")
                            skipped_count += 1
                            processed_count += 1
                            application.processed_lut_count = processed_count
                            db.session.commit()
                            continue
                        
                        # 构建LUT文件路径
                        lut_file_path = os.path.join(lut_storage_dir, lut_file.storage_path.replace('/', os.sep))
                        logger.info(f"LUT文件路径: {lut_file_path}")
                        
                        if not os.path.exists(lut_file_path):
                            error_msg = f"LUT文件不存在: {lut_file_path}"
                            logger.warning(error_msg)
                            failed_files.append({
                                'filename': lut_file.original_filename,
                                'lut_id': lut_file.id,
                                'error': error_msg
                            })
                            processed_count += 1
                            application.processed_lut_count = processed_count
                            db.session.commit()
                            continue
                        
                        # 检查LUT文件格式
                        lut_ext = os.path.splitext(lut_file_path)[1].lower()
                        if lut_ext != '.cube':
                            error_msg = f"不支持的LUT格式: {lut_ext}（当前仅支持.cube格式）"
                            logger.warning(f"LUT文件 {lut_file.original_filename} 格式不支持: {lut_ext}")
                            failed_files.append({
                                'filename': lut_file.original_filename,
                                'lut_id': lut_file.id,
                                'error': error_msg
                            })
                            processed_count += 1
                            application.processed_lut_count = processed_count
                            db.session.commit()
                            continue
                        
                        # 生成输出文件名：lut类别名_lut文件名_lut ID.jpg
                        # 获取LUT类别名（如果没有类别则使用"未分类"）
                        category_name = "未分类"
                        if lut_file.category_id:
                            # 直接查询类别表获取名称
                            category = LutCategory.query.get(lut_file.category_id)
                            if category and category.name:
                                category_name = category.name
                        logger.info(f"LUT文件 {lut_file.id} 的类别名: {category_name} (category_id: {lut_file.category_id})")
                        # 清理类别名和文件名中的特殊字符，避免文件系统问题
                        # secure_filename会移除中文字符，所以使用自定义清理逻辑
                        # 保留中文字符、字母、数字、下划线和连字符
                        category_name_clean = re.sub(r'[^\w\u4e00-\u9fff-]', '_', category_name)
                        category_name_clean = category_name_clean.replace(' ', '_').replace('/', '_').replace('\\', '_')
                        # 移除连续的下划线
                        category_name_clean = re.sub(r'_+', '_', category_name_clean).strip('_')
                        if not category_name_clean:
                            category_name_clean = "未分类"
                        
                        lut_name = os.path.splitext(lut_file.original_filename)[0]
                        # 保留中文字符、字母、数字、下划线、连字符和点号
                        lut_name_clean = re.sub(r'[^\w\u4e00-\u9fff.-]', '_', lut_name)
                        lut_name_clean = lut_name_clean.replace(' ', '_').replace('/', '_').replace('\\', '_')
                        # 移除连续的下划线
                        lut_name_clean = re.sub(r'_+', '_', lut_name_clean).strip('_')
                        if not lut_name_clean:
                            lut_name_clean = f"lut_{lut_file.id}"
                        
                        # 生成文件名：类别名_lut文件名_lut ID.jpg
                        output_filename = f"{category_name_clean}_{lut_name_clean}_{lut_file.id}.jpg"
                        logger.info(f"生成文件名: {output_filename} (类别名清理后: '{category_name_clean}', LUT名清理后: '{lut_name_clean}')")
                        output_path = os.path.join(applied_storage_dir, output_filename)
                        
                        # 应用LUT
                        logger.info(f"开始应用LUT: {lut_file.original_filename} -> {output_filename}")
                        success, error_msg = lut_service.apply_lut_to_image(
                            sample_image_path,
                            lut_file_path,
                            output_path
                        )
                        
                        if success:
                            logger.info(f"LUT应用成功: {output_filename}")
                            success_count += 1
                            # 获取输出图片信息
                            output_img = PILImage.open(output_path)
                            file_size = os.path.getsize(output_path)
                            
                            # 创建数据库记录
                            applied_image = LutAppliedImage(
                                lut_application_id=application_id,
                                lut_file_id=lut_file.id,
                                sample_image_id=sample_image_id,
                                filename=output_filename,
                                storage_path=output_filename,
                                file_size=file_size,
                                width=output_img.width,
                                height=output_img.height,
                                format='JPEG'
                            )
                            db.session.add(applied_image)
                            logger.info(f"已创建应用后图片记录: {applied_image.id}")
                        else:
                            logger.error(f"应用LUT失败: {lut_file.original_filename}, 错误: {error_msg}")
                            failed_files.append({
                                'filename': lut_file.original_filename,
                                'lut_id': lut_file.id,
                                'error': error_msg or '未知错误'
                            })
                        
                        processed_count += 1
                        application.processed_lut_count = processed_count
                        db.session.commit()
                        
                    except Exception as e:
                        error_detail = traceback.format_exc()
                        logger.error(f"处理LUT文件失败: {lut_file.original_filename}, 错误: {error_detail}")
                        failed_files.append({
                            'filename': lut_file.original_filename,
                            'lut_id': lut_file.id,
                            'error': str(e)
                        })
                        processed_count += 1
                        application.processed_lut_count = processed_count
                        db.session.commit()
                
                # 更新任务状态和错误信息
                application.status = 'completed'
                application.finished_at = datetime.now()
                
                # 构建统计信息
                stats_summary = f"总计: {total_count}, 成功: {success_count}, 跳过: {skipped_count}, 失败: {len(failed_files)}\n"
                
                # 如果有失败的文件，记录到error_message中
                if failed_files or skipped_count > 0:
                    error_summary = stats_summary
                    if skipped_count > 0:
                        error_summary += f"已跳过 {skipped_count} 个已应用过的LUT文件\n"
                    if failed_files:
                        error_summary += "\n失败的文件列表:\n"
                        for failed_file in failed_files[:50]:  # 最多显示50个失败的文件
                            error_summary += f"  - {failed_file['filename']} (ID: {failed_file['lut_id']}): {failed_file['error']}\n"
                        if len(failed_files) > 50:
                            error_summary += f"  ... 还有 {len(failed_files) - 50} 个文件失败\n"
                    application.error_message = error_summary
                    logger.info(f"LUT应用任务完成: {application_id}, {stats_summary}")
                else:
                    application.error_message = None
                    logger.info(f"LUT应用任务完成: {application_id}, 全部成功 {success_count}/{total_count} 个LUT文件")
                
                db.session.commit()
                
                logger.info(f"LUT应用任务完成: {application_id}, {stats_summary}")
                
            except Exception as e:
                error_detail = traceback.format_exc()
                logger.error(f"LUT应用任务失败: {error_detail}")
                try:
                    application = LutApplication.query.get(application_id)
                    if application:
                        application.status = 'failed'
                        application.error_message = str(e)
                        application.finished_at = datetime.now()
                        db.session.commit()
                        logger.error(f"任务状态已更新为failed: {application_id}")
                except Exception as inner_e:
                    logger.error(f"更新任务状态失败: {inner_e}")
    except Exception as outer_e:
        import traceback
        logger.error(f"LUT应用任务外层异常: {traceback.format_exc()}")

@bp.route('/<int:image_id>/apply-luts', methods=['POST'])
def apply_luts_to_image(image_id):
    """将图片应用到所有LUT文件"""
    try:
        sample_image = SampleImage.query.get_or_404(image_id)
        
        # 检查是否已有运行中的任务
        existing = LutApplication.query.filter_by(
            sample_image_id=image_id,
            status='running'
        ).first()
        
        if existing:
            return jsonify({'code': 400, 'message': '该图片已有运行中的LUT应用任务'}), 400
        
        # 创建LUT应用任务
        application = LutApplication(
            sample_image_id=image_id,
            status='pending'
        )
        db.session.add(application)
        db.session.commit()
        
        # 启动后台任务
        current_app.logger.info(f"启动LUT应用后台任务: application_id={application.id}, sample_image_id={image_id}")
        thread = threading.Thread(
            target=apply_luts_to_image_task,
            args=(application.id, image_id),
            daemon=True,
            name=f"LutApplication-{application.id}"
        )
        thread.start()
        current_app.logger.info(f"后台线程已启动: {thread.name}, thread_id={thread.ident}")
        
        return jsonify({
            'code': 200,
            'message': 'LUT应用任务已启动',
            'data': {
                'application_id': application.id
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动LUT应用任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>/lut-application-status', methods=['GET'])
def get_lut_application_status(image_id):
    """获取LUT应用任务状态"""
    try:
        # 获取最新的任务
        application = LutApplication.query.filter_by(
            sample_image_id=image_id
        ).order_by(LutApplication.created_at.desc()).first()
        
        if not application:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': application.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取LUT应用任务状态失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>/lut-applied-images', methods=['GET'])
def get_lut_applied_images(image_id):
    """获取LUT应用后的图片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        tone = request.args.get('tone', type=str)
        saturation = request.args.get('saturation', type=str)
        contrast = request.args.get('contrast', type=str)
        exclude_disliked = request.args.get('exclude_disliked', 'false').lower() == 'true'
        
        from sqlalchemy.orm import joinedload
        
        query = LutAppliedImage.query.filter_by(sample_image_id=image_id)
        
        # 如果提供了标签筛选条件，需要关联LutFileTag进行筛选
        if tone or saturation or contrast:
            tag_query = LutFileTag.query
            if tone:
                tag_query = tag_query.filter(LutFileTag.tone == tone)
            if saturation:
                tag_query = tag_query.filter(LutFileTag.saturation == saturation)
            if contrast:
                tag_query = tag_query.filter(LutFileTag.contrast == contrast)
            
            # 获取符合条件的LUT文件ID列表
            tagged_file_ids = [tag.lut_file_id for tag in tag_query.all()]
            if tagged_file_ids:
                query = query.join(LutFile).filter(LutFile.id.in_(tagged_file_ids))
            else:
                # 如果没有符合条件的标签，返回空结果
                return jsonify({
                    'code': 200,
                    'message': 'success',
                    'data': []
                })
        
        # 如果排除不喜欢的，需要过滤掉被标记为不喜欢的图片
        if exclude_disliked:
            disliked_image_ids = db.session.query(LutAppliedImagePreference.lut_applied_image_id).filter(
                LutAppliedImagePreference.is_liked == False
            ).subquery()
            query = query.filter(~LutAppliedImage.id.in_(db.session.query(disliked_image_ids)))
        
        # 使用joinedload预加载关联关系，避免N+1查询问题
        query = query.options(
            joinedload(LutAppliedImage.lut_file).joinedload(LutFile.category),
            joinedload(LutAppliedImage.lut_file).joinedload(LutFile.tags)
        )
        
        total = query.count()
        applied_images = query.order_by(LutAppliedImage.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # 获取所有图片的偏好信息（批量查询）
        image_ids = [img.id for img in applied_images]
        preferences = {}
        if image_ids:
            preference_records = LutAppliedImagePreference.query.filter(
                LutAppliedImagePreference.lut_applied_image_id.in_(image_ids)
            ).all()
            for pref in preference_records:
                preferences[pref.lut_applied_image_id] = pref.is_liked
        
        # 构建返回数据，包含LUT文件信息和美学评分
        result_list = []
        for img in applied_images:
            img_dict = img.to_dict()
            # 添加LUT文件详细信息
            if img.lut_file:
                img_dict['lut_file'] = {
                    'id': img.lut_file.id,
                    'filename': img.lut_file.filename,
                    'original_filename': img.lut_file.original_filename,
                    'category_name': img.lut_file.category.name if img.lut_file.category else None
                }
                # 添加LUT文件标签信息
                if img.lut_file.tags:
                    tag = img.lut_file.tags[0]  # 每个文件只有一个标签
                    img_dict['lut_file']['tag'] = tag.to_dict()
            # 添加美学评分信息（默认获取artimuse的评分）
            aesthetic_score = LutAppliedImageAestheticScore.query.filter_by(
                lut_applied_image_id=img.id,
                evaluator_type='artimuse'
            ).first()
            if aesthetic_score:
                img_dict['aesthetic_score'] = aesthetic_score.to_dict()
            # 添加偏好信息
            if img.id in preferences:
                img_dict['preference'] = {
                    'is_liked': preferences[img.id]
                }
            result_list.append(img_dict)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result_list
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取LUT应用后的图片列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/lut-applied-images/<int:applied_image_id>/content', methods=['GET'])
def get_lut_applied_image_content(applied_image_id):
    """获取LUT应用后的图片内容"""
    try:
        applied_image = LutAppliedImage.query.get_or_404(applied_image_id)
        
        storage_dir = get_lut_applied_image_storage_dir()
        file_path = os.path.join(storage_dir, applied_image.storage_path)
        
        if not os.path.exists(file_path):
            return jsonify({'code': 404, 'message': '文件不存在'}), 404
        
        return send_file(file_path)
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取LUT应用后的图片内容失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

def evaluate_sample_images_aesthetic_score_task(task_id, evaluator_type, score_mode):
    """后台任务：对样本图片进行美学评分"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app import create_app
        app_instance = create_app()
        with app_instance.app_context():
            try:
                task = SampleImageAestheticScoreTask.query.get(task_id)
                if not task:
                    logger.error(f"美学评分任务不存在: {task_id}")
                    return
                
                # 获取所有样本图片
                sample_images = SampleImage.query.all()
                total_count = len(sample_images)
                
                task.total_image_count = total_count
                task.status = 'running'
                db.session.commit()
                logger.info(f"开始处理样本图片美学评分，共 {total_count} 张图片")
                
                processed_count = 0
                
                for idx, sample_image in enumerate(sample_images, 1):
                    try:
                        logger.info(f"处理样本图片 [{idx}/{total_count}]: {sample_image.original_filename}")
                        
                        # 检查是否已经评分过
                        existing_score = SampleImageAestheticScore.query.filter_by(
                            sample_image_id=sample_image.id,
                            evaluator_type=evaluator_type
                        ).first()
                        
                        if existing_score:
                            processed_count += 1
                            task.processed_image_count = processed_count
                            db.session.commit()
                            logger.info(f"样本图片 {sample_image.id} 已评分过，跳过。进度: {processed_count}/{total_count}")
                            continue
                        
                        # 获取图片文件路径
                        sample_storage_dir = get_sample_image_storage_dir()
                        image_path = os.path.join(sample_storage_dir, sample_image.storage_path)
                        
                        if not os.path.exists(image_path) or not os.path.isfile(image_path):
                            logger.warning(f"样本图片文件不存在: {image_path}")
                            processed_count += 1
                            task.processed_image_count = processed_count
                            db.session.commit()
                            continue
                        
                        # 根据评分模式选择接口
                        if evaluator_type == 'artimuse':
                            if score_mode == 'score_only':
                                api_url = 'http://localhost:5001/api/evaluate_score'
                            else:
                                api_url = 'http://localhost:5001/api/evaluate'
                        else:
                            logger.error(f"Q-Insight评分器暂未实现")
                            processed_count += 1
                            task.processed_image_count = processed_count
                            db.session.commit()
                            continue
                        
                        # 调用ArtiMuse接口
                        logger.info(f"开始评分样本图片 {sample_image.id}: {image_path}")
                        
                        with open(image_path, 'rb') as f:
                            files = {'image': f}
                            response = requests.post(api_url, files=files, timeout=300)
                        
                        if response.status_code == 200:
                            try:
                                result_data = response.json()
                            except json.JSONDecodeError as e:
                                logger.error(f"评分样本图片 {sample_image.id} 失败: 无法解析JSON响应 - {response.text[:200]}")
                                processed_count += 1
                                task.processed_image_count = processed_count
                                db.session.commit()
                                continue
                            
                            # 提取分数
                            score = result_data.get('score') or result_data.get('aesthetic_score')
                            
                            if score is not None:
                                # 保存评分结果
                                aesthetic_score = SampleImageAestheticScore(
                                    sample_image_id=sample_image.id,
                                    evaluator_type=evaluator_type,
                                    score=score,
                                    details_json=json.dumps(result_data, ensure_ascii=False)
                                )
                                db.session.add(aesthetic_score)
                                logger.info(f"样本图片 {sample_image.id} 评分成功: {score}")
                            else:
                                logger.warning(f"样本图片 {sample_image.id} 评分结果中没有分数")
                        else:
                            logger.error(f"样本图片 {sample_image.id} 评分失败: HTTP {response.status_code} - {response.text[:200]}")
                        
                        processed_count += 1
                        task.processed_image_count = processed_count
                        db.session.commit()
                        logger.info(f"进度更新: {processed_count}/{total_count}")
                        
                    except requests.exceptions.ConnectionError as e:
                        logger.error(f"评分样本图片 {sample_image.id} 失败: 无法连接到ArtiMuse服务 (http://localhost:5001)，请确保服务正在运行")
                        break
                    except requests.exceptions.Timeout as e:
                        logger.error(f"评分样本图片 {sample_image.id} 失败: 请求超时（超过300秒）")
                        processed_count += 1
                        task.processed_image_count = processed_count
                        db.session.commit()
                        continue
                    except Exception as e:
                        logger.error(f"评分样本图片 {sample_image.id} 失败: {str(e)}")
                        logger.error(traceback.format_exc())
                        processed_count += 1
                        task.processed_image_count = processed_count
                        db.session.commit()
                        continue
                
                # 更新任务状态
                task.status = 'completed'
                task.finished_at = datetime.now()
                db.session.commit()
                logger.info(f"样本图片美学评分任务完成: {task_id}, 处理了 {processed_count}/{total_count} 张图片")
                
            except Exception as e:
                error_detail = traceback.format_exc()
                logger.error(f"样本图片美学评分任务失败: {error_detail}")
                try:
                    task = SampleImageAestheticScoreTask.query.get(task_id)
                    if task:
                        task.status = 'failed'
                        task.error_message = str(e)
                        task.finished_at = datetime.now()
                        db.session.commit()
                        logger.error(f"任务状态已更新为failed: {task_id}")
                except Exception as inner_e:
                    logger.error(f"更新任务状态失败: {inner_e}")
    except Exception as outer_e:
        import traceback
        logger.error(f"样本图片美学评分任务外层异常: {traceback.format_exc()}")

@bp.route('/aesthetic-score', methods=['POST'])
def start_aesthetic_score_task():
    """启动样本图片美学评分任务"""
    try:
        data = request.get_json()
        evaluator_type = data.get('evaluator_type', 'artimuse')
        score_mode = data.get('score_mode', 'score_and_reason')
        
        if evaluator_type not in ['artimuse', 'q_insight']:
            return jsonify({'code': 400, 'message': '不支持的评分器类型'}), 400
        
        if evaluator_type == 'q_insight':
            return jsonify({'code': 400, 'message': 'Q-Insight功能暂未实现'}), 400
        
        if score_mode not in ['score_only', 'score_and_reason']:
            return jsonify({'code': 400, 'message': '不支持的评分模式'}), 400
        
        # 检查是否已有运行中的任务
        existing = SampleImageAestheticScoreTask.query.filter_by(
            status='running'
        ).first()
        
        if existing:
            return jsonify({'code': 400, 'message': '已有运行中的美学评分任务'}), 400
        
        # 创建评分任务
        task = SampleImageAestheticScoreTask(
            status='pending',
            evaluator_type=evaluator_type,
            score_mode=score_mode
        )
        db.session.add(task)
        db.session.commit()
        
        # 启动后台任务
        current_app.logger.info(f"启动样本图片美学评分后台任务: task_id={task.id}, evaluator_type={evaluator_type}, score_mode={score_mode}")
        thread = threading.Thread(
            target=evaluate_sample_images_aesthetic_score_task,
            args=(task.id, evaluator_type, score_mode),
            daemon=True,
            name=f"SampleImageAestheticScore-{task.id}"
        )
        thread.start()
        current_app.logger.info(f"后台线程已启动: {thread.name}, thread_id={thread.ident}")
        
        return jsonify({
            'code': 200,
            'message': '美学评分任务已启动',
            'data': {
                'task_id': task.id
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动样本图片美学评分任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/aesthetic-score-status', methods=['GET'])
def get_aesthetic_score_status():
    """获取样本图片美学评分任务状态"""
    try:
        # 获取最新的任务
        task = SampleImageAestheticScoreTask.query.order_by(
            SampleImageAestheticScoreTask.created_at.desc()
        ).first()
        
        if not task:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': task.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取样本图片美学评分任务状态失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>/aesthetic-score', methods=['POST'])
def score_single_image(image_id):
    """对单个样本图片进行美学评分"""
    try:
        data = request.get_json() or {}
        evaluator_type = data.get('evaluator_type', 'artimuse')
        score_mode = data.get('score_mode', 'score_and_reason')
        
        if evaluator_type not in ['artimuse', 'q_insight']:
            return jsonify({'code': 400, 'message': '不支持的评分器类型'}), 400
        
        if evaluator_type == 'q_insight':
            return jsonify({'code': 400, 'message': 'Q-Insight功能暂未实现'}), 400
        
        if score_mode not in ['score_only', 'score_and_reason']:
            return jsonify({'code': 400, 'message': '不支持的评分模式'}), 400
        
        # 获取样本图片
        sample_image = SampleImage.query.get(image_id)
        if not sample_image:
            return jsonify({'code': 404, 'message': '样本图片不存在'}), 404
        
        # 检查是否已经评分过
        existing_score = SampleImageAestheticScore.query.filter_by(
            sample_image_id=image_id,
            evaluator_type=evaluator_type
        ).first()
        
        if existing_score:
            return jsonify({
                'code': 200,
                'message': '该图片已评分过',
                'data': existing_score.to_dict()
            })
        
        # 获取图片文件路径
        sample_storage_dir = get_sample_image_storage_dir()
        image_path = os.path.join(sample_storage_dir, sample_image.storage_path)
        
        if not os.path.exists(image_path) or not os.path.isfile(image_path):
            return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
        
        # 根据评分模式选择接口
        if evaluator_type == 'artimuse':
            if score_mode == 'score_only':
                api_url = 'http://localhost:5001/api/evaluate_score'
            else:
                api_url = 'http://localhost:5001/api/evaluate'
        else:
            return jsonify({'code': 400, 'message': 'Q-Insight功能暂未实现'}), 400
        
        # 调用ArtiMuse接口
        current_app.logger.info(f"开始评分样本图片 {image_id}: {image_path}")
        
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(api_url, files=files, timeout=300)
        
        if response.status_code == 200:
            try:
                result_data = response.json()
            except json.JSONDecodeError as e:
                current_app.logger.error(f"评分样本图片 {image_id} 失败: 无法解析JSON响应 - {response.text[:200]}")
                return jsonify({'code': 500, 'message': '无法解析评分结果'}), 500
            
            # 提取分数
            score = result_data.get('score') or result_data.get('aesthetic_score')
            
            if score is not None:
                # 保存评分结果
                aesthetic_score = SampleImageAestheticScore(
                    sample_image_id=image_id,
                    evaluator_type=evaluator_type,
                    score=score,
                    details_json=json.dumps(result_data, ensure_ascii=False)
                )
                db.session.add(aesthetic_score)
                db.session.commit()
                current_app.logger.info(f"样本图片 {image_id} 评分成功: {score}")
                
                return jsonify({
                    'code': 200,
                    'message': '评分成功',
                    'data': aesthetic_score.to_dict()
                })
            else:
                return jsonify({'code': 500, 'message': '评分结果中没有分数'}), 500
        else:
            current_app.logger.error(f"样本图片 {image_id} 评分失败: HTTP {response.status_code} - {response.text[:200]}")
            return jsonify({'code': 500, 'message': f'评分失败: HTTP {response.status_code}'}), 500
            
    except requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"评分样本图片 {image_id} 失败: 无法连接到ArtiMuse服务")
        return jsonify({'code': 500, 'message': '无法连接到ArtiMuse服务，请确保服务正在运行'}), 500
    except requests.exceptions.Timeout as e:
        current_app.logger.error(f"评分样本图片 {image_id} 失败: 请求超时")
        return jsonify({'code': 500, 'message': '请求超时（超过300秒）'}), 500
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"评分样本图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>/aesthetic-score', methods=['GET'])
def get_image_aesthetic_score(image_id):
    """获取样本图片的美学评分"""
    try:
        evaluator_type = request.args.get('evaluator_type', 'artimuse')
        
        score = SampleImageAestheticScore.query.filter_by(
            sample_image_id=image_id,
            evaluator_type=evaluator_type
        ).first()
        
        if not score:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': score.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取样本图片美学评分失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/lut-applied-images/<int:applied_image_id>/aesthetic-score', methods=['POST'])
def score_lut_applied_image(applied_image_id):
    """对LUT应用后的图片进行美学评分"""
    try:
        data = request.get_json() or {}
        evaluator_type = data.get('evaluator_type', 'artimuse')
        score_mode = data.get('score_mode', 'score_and_reason')
        
        if evaluator_type not in ['artimuse', 'q_insight']:
            return jsonify({'code': 400, 'message': '不支持的评分器类型'}), 400
        
        if evaluator_type == 'q_insight':
            return jsonify({'code': 400, 'message': 'Q-Insight功能暂未实现'}), 400
        
        if score_mode not in ['score_only', 'score_and_reason']:
            return jsonify({'code': 400, 'message': '不支持的评分模式'}), 400
        
        # 获取LUT应用后的图片
        applied_image = LutAppliedImage.query.get(applied_image_id)
        if not applied_image:
            return jsonify({'code': 404, 'message': 'LUT应用后的图片不存在'}), 404
        
        # 检查是否已经评分过
        existing_score = LutAppliedImageAestheticScore.query.filter_by(
            lut_applied_image_id=applied_image_id,
            evaluator_type=evaluator_type
        ).first()
        
        if existing_score:
            return jsonify({
                'code': 200,
                'message': '该图片已评分过',
                'data': existing_score.to_dict()
            })
        
        # 获取图片文件路径
        applied_storage_dir = get_lut_applied_image_storage_dir()
        image_path = os.path.join(applied_storage_dir, applied_image.storage_path)
        
        if not os.path.exists(image_path) or not os.path.isfile(image_path):
            return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
        
        # 根据评分模式选择接口
        if evaluator_type == 'artimuse':
            if score_mode == 'score_only':
                api_url = 'http://localhost:5001/api/evaluate_score'
            else:
                api_url = 'http://localhost:5001/api/evaluate'
        else:
            return jsonify({'code': 400, 'message': 'Q-Insight功能暂未实现'}), 400
        
        # 调用ArtiMuse接口
        current_app.logger.info(f"开始评分LUT应用后的图片 {applied_image_id}: {image_path}")
        
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(api_url, files=files, timeout=300)
        
        if response.status_code == 200:
            try:
                result_data = response.json()
            except json.JSONDecodeError as e:
                current_app.logger.error(f"评分LUT应用后的图片 {applied_image_id} 失败: 无法解析JSON响应 - {response.text[:200]}")
                return jsonify({'code': 500, 'message': '无法解析评分结果'}), 500
            
            # 提取分数
            score = result_data.get('score') or result_data.get('aesthetic_score')
            
            if score is not None:
                # 保存评分结果
                aesthetic_score = LutAppliedImageAestheticScore(
                    lut_applied_image_id=applied_image_id,
                    evaluator_type=evaluator_type,
                    score=score,
                    details_json=json.dumps(result_data, ensure_ascii=False)
                )
                db.session.add(aesthetic_score)
                db.session.commit()
                
                current_app.logger.info(f"LUT应用后的图片 {applied_image_id} 评分成功: {score}")
                
                return jsonify({
                    'code': 200,
                    'message': '评分成功',
                    'data': aesthetic_score.to_dict()
                })
            else:
                return jsonify({'code': 500, 'message': '评分结果中没有分数'}), 500
        else:
            current_app.logger.error(f"评分LUT应用后的图片 {applied_image_id} 失败: HTTP {response.status_code} - {response.text[:200]}")
            return jsonify({'code': 500, 'message': f'评分失败: HTTP {response.status_code}'}), 500
            
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"评分LUT应用后的图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/lut-applied-images/<int:applied_image_id>/aesthetic-score', methods=['GET'])
def get_lut_applied_image_aesthetic_score(applied_image_id):
    """获取LUT应用后图片的美学评分"""
    try:
        evaluator_type = request.args.get('evaluator_type', 'artimuse')
        
        score = LutAppliedImageAestheticScore.query.filter_by(
            lut_applied_image_id=applied_image_id,
            evaluator_type=evaluator_type
        ).first()
        
        if not score:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': score.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取LUT应用后图片美学评分失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

def evaluate_lut_applied_images_aesthetic_score_task(task_id, sample_image_id, evaluator_type, score_mode):
    """后台任务：对样本图片的所有LUT应用后的图片进行美学评分"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app import create_app
        app_instance = create_app()
        with app_instance.app_context():
            try:
                task = LutAppliedImageAestheticScoreTask.query.get(task_id)
                if not task:
                    logger.error(f"美学评分任务不存在: {task_id}")
                    return
                
                # 获取该样本图片的所有LUT应用后的图片
                applied_images = LutAppliedImage.query.filter_by(sample_image_id=sample_image_id).all()
                total_count = len(applied_images)
                
                task.total_image_count = total_count
                task.status = 'running'
                db.session.commit()
                logger.info(f"开始处理LUT应用后图片美学评分，共 {total_count} 张图片")
                
                if total_count == 0:
                    task.status = 'completed'
                    task.finished_at = datetime.now()
                    db.session.commit()
                    logger.info("没有LUT应用后的图片需要评分")
                    return
                
                processed_count = 0
                applied_storage_dir = get_lut_applied_image_storage_dir()
                
                # 根据评分模式选择接口
                if evaluator_type == 'artimuse':
                    if score_mode == 'score_only':
                        api_url = 'http://localhost:5001/api/evaluate_score'
                    else:
                        api_url = 'http://localhost:5001/api/evaluate'
                else:
                    task.status = 'failed'
                    task.error_message = 'Q-Insight功能暂未实现'
                    task.finished_at = datetime.now()
                    db.session.commit()
                    return
                
                for applied_image in applied_images:
                    try:
                        # 检查是否已经评分过
                        existing_score = LutAppliedImageAestheticScore.query.filter_by(
                            lut_applied_image_id=applied_image.id,
                            evaluator_type=evaluator_type
                        ).first()
                        
                        if existing_score:
                            logger.info(f"LUT应用后的图片 {applied_image.id} 已评分过，跳过")
                            processed_count += 1
                            task.processed_image_count = processed_count
                            db.session.commit()
                            continue
                        
                        # 获取图片文件路径
                        image_path = os.path.join(applied_storage_dir, applied_image.storage_path)
                        
                        if not os.path.exists(image_path) or not os.path.isfile(image_path):
                            logger.warning(f"LUT应用后的图片文件不存在: {image_path}")
                            processed_count += 1
                            task.processed_image_count = processed_count
                            db.session.commit()
                            continue
                        
                        # 调用ArtiMuse接口
                        logger.info(f"开始评分LUT应用后的图片 {applied_image.id}: {image_path}")
                        
                        with open(image_path, 'rb') as f:
                            files = {'image': f}
                            response = requests.post(api_url, files=files, timeout=300)
                        
                        if response.status_code == 200:
                            try:
                                result_data = response.json()
                            except json.JSONDecodeError as e:
                                logger.error(f"评分LUT应用后的图片 {applied_image.id} 失败: 无法解析JSON响应 - {response.text[:200]}")
                                processed_count += 1
                                task.processed_image_count = processed_count
                                db.session.commit()
                                continue
                            
                            # 提取分数
                            score = result_data.get('score') or result_data.get('aesthetic_score')
                            
                            if score is not None:
                                # 保存评分结果
                                aesthetic_score = LutAppliedImageAestheticScore(
                                    lut_applied_image_id=applied_image.id,
                                    evaluator_type=evaluator_type,
                                    score=score,
                                    details_json=json.dumps(result_data, ensure_ascii=False)
                                )
                                db.session.add(aesthetic_score)
                                logger.info(f"LUT应用后的图片 {applied_image.id} 评分成功: {score}")
                            else:
                                logger.warning(f"LUT应用后的图片 {applied_image.id} 评分结果中没有分数")
                        else:
                            logger.error(f"评分LUT应用后的图片 {applied_image.id} 失败: HTTP {response.status_code} - {response.text[:200]}")
                        
                        processed_count += 1
                        task.processed_image_count = processed_count
                        db.session.commit()
                        logger.info(f"进度更新: {processed_count}/{total_count}")
                        
                    except requests.exceptions.ConnectionError as e:
                        logger.error(f"评分LUT应用后的图片 {applied_image.id} 失败: 无法连接到ArtiMuse服务 (http://localhost:5001)，请确保服务正在运行")
                        processed_count += 1
                        task.processed_image_count = processed_count
                        db.session.commit()
                        continue
                    except Exception as e:
                        logger.error(f"评分LUT应用后的图片 {applied_image.id} 失败: {str(e)}")
                        logger.error(traceback.format_exc())
                        processed_count += 1
                        task.processed_image_count = processed_count
                        db.session.commit()
                        continue
                
                # 更新任务状态
                task.status = 'completed'
                task.finished_at = datetime.now()
                db.session.commit()
                
                logger.info(f"LUT应用后图片美学评分任务完成: {task_id}, 处理了 {processed_count}/{total_count} 张图片")
                
            except Exception as e:
                error_detail = traceback.format_exc()
                logger.error(f"LUT应用后图片美学评分任务失败: {error_detail}")
                try:
                    task = LutAppliedImageAestheticScoreTask.query.get(task_id)
                    if task:
                        task.status = 'failed'
                        task.error_message = str(e)
                        task.finished_at = datetime.now()
                        db.session.commit()
                        logger.error(f"任务状态已更新为failed: {task_id}")
                except Exception as inner_e:
                    logger.error(f"更新任务状态失败: {inner_e}")
    except Exception as outer_e:
        import traceback
        logger.error(f"LUT应用后图片美学评分任务外层异常: {traceback.format_exc()}")

@bp.route('/<int:image_id>/lut-applied-images/aesthetic-score', methods=['POST'])
def start_lut_applied_images_aesthetic_score(image_id):
    """启动对样本图片的所有LUT应用后的图片进行批量美学评分"""
    try:
        data = request.get_json() or {}
        evaluator_type = data.get('evaluator_type', 'artimuse')
        score_mode = data.get('score_mode', 'score_and_reason')
        
        if evaluator_type not in ['artimuse', 'q_insight']:
            return jsonify({'code': 400, 'message': '不支持的评分器类型'}), 400
        
        if evaluator_type == 'q_insight':
            return jsonify({'code': 400, 'message': 'Q-Insight功能暂未实现'}), 400
        
        if score_mode not in ['score_only', 'score_and_reason']:
            return jsonify({'code': 400, 'message': '不支持的评分模式'}), 400
        
        # 检查是否已有运行中的任务
        existing = LutAppliedImageAestheticScoreTask.query.filter_by(
            sample_image_id=image_id,
            status='running'
        ).first()
        
        if existing:
            return jsonify({'code': 400, 'message': '该图片已有运行中的美学评分任务'}), 400
        
        # 创建评分任务
        task = LutAppliedImageAestheticScoreTask(
            sample_image_id=image_id,
            status='pending',
            evaluator_type=evaluator_type,
            score_mode=score_mode
        )
        db.session.add(task)
        db.session.commit()
        
        # 启动后台任务
        current_app.logger.info(f"启动LUT应用后图片美学评分后台任务: task_id={task.id}, sample_image_id={image_id}, evaluator_type={evaluator_type}, score_mode={score_mode}")
        thread = threading.Thread(
            target=evaluate_lut_applied_images_aesthetic_score_task,
            args=(task.id, image_id, evaluator_type, score_mode),
            daemon=True,
            name=f"LutAppliedImageAestheticScore-{task.id}"
        )
        thread.start()
        current_app.logger.info(f"后台线程已启动: {thread.name}, thread_id={thread.ident}")
        
        return jsonify({
            'code': 200,
            'message': '美学评分任务已启动',
            'data': {
                'task_id': task.id
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动LUT应用后图片美学评分任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:image_id>/lut-applied-images/aesthetic-score-status', methods=['GET'])
def get_lut_applied_images_aesthetic_score_status(image_id):
    """获取LUT应用后图片美学评分任务状态"""
    try:
        # 获取最新的任务
        task = LutAppliedImageAestheticScoreTask.query.filter_by(
            sample_image_id=image_id
        ).order_by(LutAppliedImageAestheticScoreTask.created_at.desc()).first()
        
        if not task:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': task.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取LUT应用后图片美学评分任务状态失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/lut-applied-images/<int:applied_image_id>/preference', methods=['POST'])
def set_lut_applied_image_preference(applied_image_id):
    """设置LUT应用结果图片的偏好（喜欢/不喜欢）"""
    try:
        data = request.get_json() or {}
        is_liked = data.get('is_liked')
        
        if is_liked is None:
            return jsonify({'code': 400, 'message': '缺少is_liked参数'}), 400
        
        if not isinstance(is_liked, bool):
            return jsonify({'code': 400, 'message': 'is_liked必须是布尔值'}), 400
        
        # 检查图片是否存在
        applied_image = LutAppliedImage.query.get(applied_image_id)
        if not applied_image:
            return jsonify({'code': 404, 'message': 'LUT应用结果图片不存在'}), 404
        
        # 查找或创建偏好记录
        preference = LutAppliedImagePreference.query.filter_by(
            lut_applied_image_id=applied_image_id
        ).first()
        
        if preference:
            # 更新现有记录
            preference.is_liked = is_liked
            preference.updated_at = datetime.now()
        else:
            # 创建新记录
            preference = LutAppliedImagePreference(
                lut_applied_image_id=applied_image_id,
                is_liked=is_liked
            )
            db.session.add(preference)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '偏好设置成功',
            'data': preference.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"设置LUT应用结果图片偏好失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/lut-applied-images/<int:applied_image_id>/preference', methods=['DELETE'])
def delete_lut_applied_image_preference(applied_image_id):
    """删除LUT应用结果图片的偏好（取消喜欢/不喜欢）"""
    try:
        preference = LutAppliedImagePreference.query.filter_by(
            lut_applied_image_id=applied_image_id
        ).first()
        
        if not preference:
            return jsonify({'code': 404, 'message': '偏好记录不存在'}), 404
        
        db.session.delete(preference)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '偏好删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除LUT应用结果图片偏好失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
