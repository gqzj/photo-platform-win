# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app, send_file
from app.database import db
from app.models.lut_file import LutFile
from app.models.lut_category import LutCategory
from app.models.lut_file_tag import LutFileTag
from app.models.lut_file_analysis_task import LutFileAnalysisTask
from app.models.lut_cluster import LutCluster
from app.models.lut_cluster_snapshot import LutClusterSnapshot
from app.utils.config_manager import get_local_image_dir
from app.services.lut_analysis_service import LutAnalysisService
from werkzeug.utils import secure_filename
import traceback
import os
import hashlib
import json
import re
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('lut_file', __name__)

# 允许的Lut文件扩展名
ALLOWED_EXTENSIONS = {'cube', '3dl', 'csp', 'look', 'mga', 'm3d'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_lut_storage_dir():
    """获取Lut文件存储目录"""
    base_dir = get_local_image_dir()
    lut_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'luts')
    os.makedirs(lut_dir, exist_ok=True)
    return lut_dir

def get_lut_thumbnail_dir():
    """获取LUT缩略图存储目录"""
    base_dir = get_local_image_dir()
    thumbnail_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'lut_thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)
    return thumbnail_dir

def generate_lut_thumbnail(lut_file_id, lut_file_path):
    """
    生成LUT文件的缩略图（应用LUT到lut_standard.png）
    
    Args:
        lut_file_id: LUT文件ID
        lut_file_path: LUT文件路径
    
    Returns:
        缩略图路径（相对于存储目录）或None
    """
    try:
        # 查找lut_standard.png文件（在backend目录下）
        current_file = os.path.abspath(__file__)
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        standard_image_path = os.path.join(backend_dir, 'lut_standard.png')
        
        if not os.path.exists(standard_image_path):
            # 如果lut_standard.png不存在，尝试standard.png
            standard_image_path = os.path.join(backend_dir, 'standard.png')
            if not os.path.exists(standard_image_path):
                current_app.logger.warning(f"标准图文件不存在: lut_standard.png 或 standard.png")
                return None
        
        # 应用LUT到标准图
        from app.services.lut_application_service import LutApplicationService
        lut_service = LutApplicationService()
        
        # 生成缩略图路径
        thumbnail_dir = get_lut_thumbnail_dir()
        thumbnail_filename = f"thumbnail_{lut_file_id}.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
        
        success, error_msg = lut_service.apply_lut_to_image(
            standard_image_path,
            lut_file_path,
            thumbnail_path
        )
        
        if success:
            # 返回相对路径
            relative_path = f"lut_thumbnails/{thumbnail_filename}"
            current_app.logger.info(f"LUT文件 {lut_file_id} 缩略图生成成功: {relative_path}")
            return relative_path
        else:
            current_app.logger.error(f"LUT文件 {lut_file_id} 缩略图生成失败: {error_msg}")
            return None
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"生成LUT缩略图失败: {error_detail}")
        return None

def calculate_file_hash(file_path):
    """计算文件哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

@bp.route('', methods=['GET'])
def get_lut_file_list():
    """获取Lut文件列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        category_id = request.args.get('category_id', type=int)
        keyword = request.args.get('keyword', type=str)
        tone = request.args.get('tone', type=str)
        saturation = request.args.get('saturation', type=str)
        contrast = request.args.get('contrast', type=str)
        
        from sqlalchemy.orm import joinedload
        
        query = LutFile.query.options(joinedload(LutFile.tags))
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if keyword:
            query = query.filter(
                db.or_(
                    LutFile.filename.like(f'%{keyword}%'),
                    LutFile.original_filename.like(f'%{keyword}%')
                )
            )
        
        # 标签筛选
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
                query = query.filter(LutFile.id.in_(tagged_file_ids))
            else:
                # 如果没有符合条件的标签，返回空结果
                return jsonify({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'list': [],
                        'total': 0,
                        'page': page,
                        'page_size': page_size
                    }
                })
        
        total = query.count()
        files = query.order_by(LutFile.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # 构建返回数据，包含标签信息
        result_list = []
        for f in files:
            file_dict = f.to_dict()
            # 添加标签信息
            if f.tags:
                tag = f.tags[0]  # 每个文件只有一个标签
                file_dict['tag'] = tag.to_dict()
            result_list.append(file_dict)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': result_list,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取Lut文件列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:file_id>', methods=['GET'])
def get_lut_file(file_id):
    """获取Lut文件详情"""
    try:
        lut_file = LutFile.query.get_or_404(file_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': lut_file.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取Lut文件详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def upload_lut_files():
    """批量上传Lut文件"""
    try:
        if 'files' not in request.files:
            return jsonify({'code': 400, 'message': '没有上传文件'}), 400
        
        files = request.files.getlist('files')
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '')
        custom_filenames_str = request.form.get('custom_filenames', '')
        
        if not files or len(files) == 0:
            return jsonify({'code': 400, 'message': '文件列表为空'}), 400
        
        # 解析自定义文件名列表
        custom_filenames = []
        if custom_filenames_str:
            try:
                custom_filenames = json.loads(custom_filenames_str)
            except:
                custom_filenames = []
        
        # 验证分类是否存在
        if category_id:
            category = LutCategory.query.get(category_id)
            if not category:
                return jsonify({'code': 400, 'message': '分类不存在'}), 400
        
        uploaded_files = []
        errors = []
        
        storage_dir = get_lut_storage_dir()
        
        for idx, file in enumerate(files):
            if file.filename == '':
                errors.append({'filename': '', 'error': '文件名为空'})
                continue
            
            if not allowed_file(file.filename):
                errors.append({'filename': file.filename, 'error': f'不支持的文件类型，仅支持: {", ".join(ALLOWED_EXTENSIONS)}'})
                continue
            
            try:
                # 如果提供了自定义文件名列表，使用自定义文件名；否则使用原始文件名
                if idx < len(custom_filenames) and custom_filenames[idx]:
                    original_filename = custom_filenames[idx]
                else:
                    original_filename = file.filename
                
                # 提取文件扩展名
                file_ext = ''
                if '.' in original_filename:
                    file_ext = '.' + original_filename.rsplit('.', 1)[1].lower()
                    base_name = original_filename.rsplit('.', 1)[0]
                else:
                    base_name = original_filename
                
                # 清理文件名，保留中文字符、字母、数字、下划线、连字符和点号
                # 移除其他特殊字符，避免文件系统问题
                filename_clean = re.sub(r'[^\w\u4e00-\u9fff.-]', '_', base_name)
                filename_clean = filename_clean.replace(' ', '_').replace('/', '_').replace('\\', '_')
                # 移除连续的下划线
                filename_clean = re.sub(r'_+', '_', filename_clean).strip('_')
                if not filename_clean:
                    filename_clean = f"file_{idx}"
                
                # 拼接扩展名
                filename = filename_clean + file_ext
                
                # 生成唯一文件名（避免重名）
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{os.urandom(4).hex()}_{filename}"
                
                # 如果指定了分类，创建分类子目录
                if category_id:
                    category_dir = os.path.join(storage_dir, str(category_id))
                    os.makedirs(category_dir, exist_ok=True)
                    file_path = os.path.join(category_dir, unique_filename)
                    relative_path = os.path.join(str(category_id), unique_filename).replace('\\', '/')
                else:
                    file_path = os.path.join(storage_dir, unique_filename)
                    relative_path = unique_filename
                
                # 保存文件
                file.save(file_path)
                
                # 计算文件大小和哈希值
                file_size = os.path.getsize(file_path)
                file_hash = calculate_file_hash(file_path)
                
                # 检查是否已存在相同哈希的文件
                existing_hash = LutFile.query.filter_by(file_hash=file_hash).first()
                if existing_hash:
                    # 删除刚上传的文件
                    os.remove(file_path)
                    errors.append({'filename': original_filename, 'error': '文件已存在（相同哈希值）'})
                    continue
                
                # 检查是否已存在相同的category_id和original_filename组合
                existing_unique = LutFile.query.filter_by(
                    category_id=category_id,
                    original_filename=original_filename
                ).first()
                if existing_unique:
                    # 删除刚上传的文件
                    os.remove(file_path)
                    category_name = existing_unique.category.name if existing_unique.category else '未分类'
                    errors.append({'filename': original_filename, 'error': f'该类别下已存在同名文件（类别: {category_name}）'})
                    continue
                
                # 创建数据库记录
                lut_file = LutFile(
                    category_id=category_id,
                    filename=unique_filename,
                    original_filename=original_filename,
                    storage_path=relative_path,
                    file_size=file_size,
                    file_hash=file_hash,
                    description=description
                )
                
                db.session.add(lut_file)
                uploaded_files.append(lut_file)
                
            except Exception as e:
                errors.append({'filename': file.filename, 'error': str(e)})
                current_app.logger.error(f"上传文件失败: {file.filename}, 错误: {traceback.format_exc()}")
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功上传 {len(uploaded_files)} 个文件',
            'data': {
                'uploaded': [f.to_dict() for f in uploaded_files],
                'errors': errors
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量上传Lut文件失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:file_id>', methods=['PUT'])
def update_lut_file(file_id):
    """更新Lut文件信息"""
    try:
        lut_file = LutFile.query.get_or_404(file_id)
        data = request.get_json()
        
        original_filename = data.get('original_filename')
        category_id = data.get('category_id')
        description = data.get('description')
        
        # 检查是否需要更新original_filename或category_id
        need_check_unique = False
        new_category_id = lut_file.category_id
        new_original_filename = lut_file.original_filename
        
        if original_filename is not None:
            if not original_filename.strip():
                return jsonify({'code': 400, 'message': '原始文件名不能为空'}), 400
            new_original_filename = original_filename.strip()
            if new_original_filename != lut_file.original_filename:
                need_check_unique = True
                lut_file.original_filename = new_original_filename
        
        if category_id is not None:
            if category_id:
                category = LutCategory.query.get(category_id)
                if not category:
                    return jsonify({'code': 400, 'message': '分类不存在'}), 400
            new_category_id = category_id
            if new_category_id != lut_file.category_id:
                need_check_unique = True
                lut_file.category_id = category_id
        
        # 如果修改了category_id或original_filename，检查唯一约束
        if need_check_unique:
            existing_unique = LutFile.query.filter(
                LutFile.id != file_id,
                LutFile.category_id == new_category_id,
                LutFile.original_filename == new_original_filename
            ).first()
            if existing_unique:
                db.session.rollback()
                category_name = existing_unique.category.name if existing_unique.category else '未分类'
                return jsonify({'code': 400, 'message': f'该类别下已存在同名文件（类别: {category_name}）'}), 400
        
        if description is not None:
            lut_file.description = description
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': lut_file.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新Lut文件失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:file_id>', methods=['DELETE'])
def delete_lut_file(file_id):
    """删除Lut文件"""
    try:
        lut_file = LutFile.query.get_or_404(file_id)
        
        # 删除物理文件
        storage_dir = get_lut_storage_dir()
        file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                current_app.logger.warning(f"删除物理文件失败: {file_path}, 错误: {e}")
        
        # 删除数据库记录
        db.session.delete(lut_file)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除Lut文件失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:file_id>/download', methods=['GET'])
def download_lut_file(file_id):
    """下载Lut文件"""
    try:
        lut_file = LutFile.query.get_or_404(file_id)
        
        storage_dir = get_lut_storage_dir()
        file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
        
        if not os.path.exists(file_path):
            return jsonify({'code': 404, 'message': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=lut_file.original_filename)
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"下载Lut文件失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:file_id>/analyze', methods=['POST'])
def analyze_lut_file(file_id):
    """分析LUT文件并生成标签"""
    try:
        lut_file = LutFile.query.get_or_404(file_id)
        
        # 检查文件扩展名，目前只支持.cube格式
        if not lut_file.original_filename.lower().endswith('.cube'):
            return jsonify({'code': 400, 'message': '目前只支持.cube格式的LUT文件分析'}), 400
        
        # 获取文件路径
        storage_dir = get_lut_storage_dir()
        file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
        
        if not os.path.exists(file_path):
            return jsonify({'code': 404, 'message': '文件不存在'}), 404
        
        # 分析LUT文件
        analysis_service = LutAnalysisService()
        analysis_result = analysis_service.analyze_lut(file_path)
        
        if analysis_result is None:
            return jsonify({'code': 500, 'message': '分析失败，无法解析LUT文件'}), 500
        
        # 保存或更新标签
        existing_tag = LutFileTag.query.filter_by(lut_file_id=file_id).first()
        
        if existing_tag:
            # 更新现有标签
            existing_tag.tone = analysis_result.get('tone')
            existing_tag.saturation = analysis_result.get('saturation')
            existing_tag.contrast = analysis_result.get('contrast')
            existing_tag.h_mean = analysis_result.get('h_mean')
            existing_tag.s_mean = analysis_result.get('s_mean')
            existing_tag.s_var = analysis_result.get('s_var')
            existing_tag.v_var = analysis_result.get('v_var')
            existing_tag.contrast_rgb = analysis_result.get('contrast_rgb')
            db.session.commit()
            tag = existing_tag
        else:
            # 创建新标签
            tag = LutFileTag(
                lut_file_id=file_id,
                tone=analysis_result.get('tone'),
                saturation=analysis_result.get('saturation'),
                contrast=analysis_result.get('contrast'),
                h_mean=analysis_result.get('h_mean'),
                s_mean=analysis_result.get('s_mean'),
                s_var=analysis_result.get('s_var'),
                v_var=analysis_result.get('v_var'),
                contrast_rgb=analysis_result.get('contrast_rgb')
            )
            db.session.add(tag)
            db.session.commit()
        
        # 生成缩略图（如果还没有）
        if not lut_file.thumbnail_path:
            thumbnail_path = generate_lut_thumbnail(file_id, file_path)
            if thumbnail_path:
                lut_file.thumbnail_path = thumbnail_path
                db.session.commit()
        
        current_app.logger.info(f"LUT文件 {file_id} 分析完成: {analysis_result}")
        
        return jsonify({
            'code': 200,
            'message': '分析成功',
            'data': tag.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"分析LUT文件失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

def batch_analyze_lut_files_task(task_id, skip_analyzed=True):
    """后台任务：批量分析LUT文件"""
    try:
        from app import create_app
        app_instance = create_app()
        with app_instance.app_context():
            try:
                task = LutFileAnalysisTask.query.get(task_id)
                if not task:
                    logger.error(f"批量分析任务不存在: {task_id}")
                    return
                
                # 获取所有.cube格式的LUT文件
                query = LutFile.query.filter(
                    db.func.lower(LutFile.original_filename).like('%.cube')
                )
                
                # 如果跳过已分析的文件，只获取没有标签的文件
                if skip_analyzed:
                    # 获取已有标签的文件ID列表
                    analyzed_file_ids = db.session.query(LutFileTag.lut_file_id).distinct().all()
                    analyzed_file_ids = [fid[0] for fid in analyzed_file_ids]
                    if analyzed_file_ids:
                        query = query.filter(~LutFile.id.in_(analyzed_file_ids))
                
                lut_files = query.all()
                total_count = len(lut_files)
                
                task.total_file_count = total_count
                task.status = 'running'
                db.session.commit()
                logger.info(f"开始批量分析LUT文件，共 {total_count} 个文件")
                
                if total_count == 0:
                    task.status = 'completed'
                    task.finished_at = datetime.now()
                    db.session.commit()
                    logger.info("没有.cube格式的LUT文件需要分析")
                    return
                
                processed_count = 0
                success_count = 0
                failed_count = 0
                storage_dir = get_lut_storage_dir()
                analysis_service = LutAnalysisService()
                
                def check_interrupted():
                    """检查任务是否被中断"""
                    db.session.expire(task)
                    db.session.refresh(task)
                    return task.interrupted
                
                for lut_file in lut_files:
                    # 检查是否被中断（循环开始时）
                    if check_interrupted():
                        logger.info(f"任务被中断，停止处理。已处理: {processed_count}/{total_count}")
                        task.status = 'failed'
                        task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                        task.finished_at = datetime.now()
                        db.session.commit()
                        return
                    
                    try:
                        # 获取文件路径
                        file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
                        
                        if not os.path.exists(file_path):
                            logger.warning(f"LUT文件不存在: {file_path}")
                            failed_count += 1
                            processed_count += 1
                            task.processed_file_count = processed_count
                            task.failed_count = failed_count
                            db.session.commit()
                            # 检查中断（文件不存在后）
                            if check_interrupted():
                                logger.info(f"任务被中断，停止处理。已处理: {processed_count}/{total_count}")
                                task.status = 'failed'
                                task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                                task.finished_at = datetime.now()
                                db.session.commit()
                                return
                            continue
                        
                        # 检查中断（分析文件前）
                        if check_interrupted():
                            logger.info(f"任务被中断，停止处理。已处理: {processed_count}/{total_count}")
                            task.status = 'failed'
                            task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                            task.finished_at = datetime.now()
                            db.session.commit()
                            return
                        
                        # 分析LUT文件（传入中断检查函数）
                        try:
                            analysis_result = analysis_service.analyze_lut(file_path, check_interrupted=check_interrupted)
                        except InterruptedError:
                            # 分析过程中被中断
                            logger.info(f"分析过程中被中断，停止处理。已处理: {processed_count}/{total_count}")
                            task.status = 'failed'
                            task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                            task.finished_at = datetime.now()
                            db.session.commit()
                            return
                        
                        # 检查中断（分析文件后）
                        if check_interrupted():
                            logger.info(f"任务被中断，停止处理。已处理: {processed_count}/{total_count}")
                            task.status = 'failed'
                            task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                            task.finished_at = datetime.now()
                            db.session.commit()
                            return
                        
                        if analysis_result is None:
                            logger.warning(f"无法分析LUT文件: {lut_file.original_filename}")
                            failed_count += 1
                            processed_count += 1
                            task.processed_file_count = processed_count
                            task.failed_count = failed_count
                            db.session.commit()
                            # 检查中断（分析失败后）
                            if check_interrupted():
                                logger.info(f"任务被中断，停止处理。已处理: {processed_count}/{total_count}")
                                task.status = 'failed'
                                task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                                task.finished_at = datetime.now()
                                db.session.commit()
                                return
                            continue
                        
                        # 保存或更新标签
                        existing_tag = LutFileTag.query.filter_by(lut_file_id=lut_file.id).first()
                        
                        if existing_tag:
                            # 更新现有标签
                            existing_tag.tone = analysis_result.get('tone')
                            existing_tag.saturation = analysis_result.get('saturation')
                            existing_tag.contrast = analysis_result.get('contrast')
                            existing_tag.h_mean = analysis_result.get('h_mean')
                            existing_tag.s_mean = analysis_result.get('s_mean')
                            existing_tag.s_var = analysis_result.get('s_var')
                            existing_tag.v_var = analysis_result.get('v_var')
                            existing_tag.contrast_rgb = analysis_result.get('contrast_rgb')
                        else:
                            # 创建新标签
                            tag = LutFileTag(
                                lut_file_id=lut_file.id,
                                tone=analysis_result.get('tone'),
                                saturation=analysis_result.get('saturation'),
                                contrast=analysis_result.get('contrast'),
                                h_mean=analysis_result.get('h_mean'),
                                s_mean=analysis_result.get('s_mean'),
                                s_var=analysis_result.get('s_var'),
                                v_var=analysis_result.get('v_var'),
                                contrast_rgb=analysis_result.get('contrast_rgb')
                            )
                            db.session.add(tag)
                        
                        # 生成缩略图（如果还没有）
                        if not lut_file.thumbnail_path:
                            thumbnail_path = generate_lut_thumbnail(lut_file.id, file_path)
                            if thumbnail_path:
                                lut_file.thumbnail_path = thumbnail_path
                        
                        success_count += 1
                        processed_count += 1
                        task.processed_file_count = processed_count
                        task.success_count = success_count
                        db.session.commit()
                        logger.info(f"进度更新: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}")
                        
                        # 检查中断（保存成功后）
                        if check_interrupted():
                            logger.info(f"任务被中断，停止处理。已处理: {processed_count}/{total_count}")
                            task.status = 'failed'
                            task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                            task.finished_at = datetime.now()
                            db.session.commit()
                            return
                        
                    except Exception as e:
                        logger.error(f"分析LUT文件 {lut_file.id} 失败: {str(e)}")
                        logger.error(traceback.format_exc())
                        failed_count += 1
                        processed_count += 1
                        task.processed_file_count = processed_count
                        task.failed_count = failed_count
                        db.session.commit()
                        # 检查中断（异常处理后）
                        if check_interrupted():
                            logger.info(f"任务被中断，停止处理。已处理: {processed_count}/{total_count}")
                            task.status = 'failed'
                            task.error_message = f"任务被用户中断。已处理: {processed_count}/{total_count}, 成功: {success_count}, 失败: {failed_count}"
                            task.finished_at = datetime.now()
                            db.session.commit()
                            return
                        continue
                
                # 更新任务状态
                task.status = 'completed'
                task.finished_at = datetime.now()
                if failed_count > 0:
                    task.error_message = f"成功: {success_count}, 失败: {failed_count}"
                db.session.commit()
                logger.info(f"批量分析LUT文件完成: 成功 {success_count}, 失败 {failed_count}")
                
            except Exception as e:
                logger.error(f"批量分析LUT文件任务内层异常: {str(e)}")
                logger.error(traceback.format_exc())
                task = LutFileAnalysisTask.query.get(task_id)
                if task:
                    task.status = 'failed'
                    task.error_message = str(e)
                    task.finished_at = datetime.now()
                    db.session.commit()
    except Exception as e:
        logger.error(f"批量分析LUT文件任务外层异常: {traceback.format_exc()}")

@bp.route('/batch-analyze', methods=['POST'])
def start_batch_analyze():
    """启动批量分析LUT文件任务"""
    try:
        data = request.get_json() or {}
        skip_analyzed = data.get('skip_analyzed', True)  # 默认跳过已分析的文件
        force_restart = data.get('force_restart', False)  # 是否强制重新启动
        
        # 检查是否已有运行中的任务
        existing_running = LutFileAnalysisTask.query.filter_by(
            status='running'
        ).first()
        
        if existing_running and not force_restart:
            return jsonify({'code': 400, 'message': '已有运行中的批量分析任务，如需重新启动请设置force_restart=true'}), 400
        
        # 如果强制重新启动，将运行中的任务标记为失败
        if existing_running and force_restart:
            existing_running.status = 'failed'
            existing_running.error_message = '任务被用户强制重新启动'
            existing_running.finished_at = datetime.now()
            db.session.commit()
            current_app.logger.info(f"已停止运行中的任务: {existing_running.id}")
        
        # 创建分析任务
        task = LutFileAnalysisTask(
            status='pending'
        )
        db.session.add(task)
        db.session.commit()
        
        # 启动后台任务
        current_app.logger.info(f"启动批量分析LUT文件后台任务: task_id={task.id}, skip_analyzed={skip_analyzed}")
        thread = threading.Thread(
            target=batch_analyze_lut_files_task,
            args=(task.id, skip_analyzed),
            daemon=True,
            name=f"LutFileBatchAnalyze-{task.id}"
        )
        thread.start()
        current_app.logger.info(f"后台线程已启动: {thread.name}, thread_id={thread.ident}")
        
        return jsonify({
            'code': 200,
            'message': '批量分析任务已启动',
            'data': {
                'task_id': task.id
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动批量分析LUT文件任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch-analyze-status', methods=['GET'])
def get_batch_analyze_status():
    """获取批量分析任务状态"""
    try:
        # 获取最新的任务
        task = LutFileAnalysisTask.query.order_by(LutFileAnalysisTask.id.desc()).first()
        
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
        current_app.logger.error(f"获取批量分析任务状态失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/test-analyze', methods=['POST'])
def test_analyze_lut_file():
    """测试分析LUT文件（上传文件并分析，不保存到数据库）"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': 400, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 400, 'message': '文件名为空'}), 400
        
        # 检查文件扩展名
        if not allowed_file(file.filename):
            return jsonify({'code': 400, 'message': '不支持的文件格式，仅支持: .cube, .3dl, .csp, .look, .mga, .m3d'}), 400
        
        # 检查文件扩展名，目前只支持.cube格式的分析
        if not file.filename.lower().endswith('.cube'):
            return jsonify({'code': 400, 'message': '目前只支持.cube格式的LUT文件分析'}), 400
        
        # 获取分析方式
        analysis_mode = request.form.get('mode', 'direct')  # 'direct' 或 'standard-image'
        
        # 创建临时目录保存文件
        temp_dir = os.path.join(get_lut_storage_dir(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存临时文件
        temp_filename = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        temp_file_path = os.path.join(temp_dir, temp_filename)
        file.save(temp_file_path)
        
        try:
            analysis_service = LutAnalysisService()
            
            if analysis_mode == 'standard-image':
                # 使用标准图方式分析
                # 查找standard.png文件（在backend目录下）
                # __file__ 是 backend/app/api/lut_file.py
                # 向上三级目录找到backend目录
                current_file = os.path.abspath(__file__)
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                standard_image_path = os.path.join(backend_dir, 'standard.png')
                
                if not os.path.exists(standard_image_path):
                    # 删除临时文件
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    return jsonify({'code': 404, 'message': '标准图文件不存在: standard.png'}), 404
                
                # 应用LUT到标准图
                from app.services.lut_application_service import LutApplicationService
                lut_service = LutApplicationService()
                
                # 生成临时输出图片路径
                output_image_path = os.path.join(temp_dir, f"output_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                
                success, error_msg = lut_service.apply_lut_to_image(
                    standard_image_path,
                    temp_file_path,
                    output_image_path
                )
                
                if not success:
                    # 删除临时文件
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    return jsonify({'code': 500, 'message': f'应用LUT到标准图失败: {error_msg}'}), 500
                
                # 分析结果图
                analysis_result = analysis_service.analyze_image(output_image_path)
                
                # 删除临时文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if os.path.exists(output_image_path):
                    os.remove(output_image_path)
                
                if analysis_result is None:
                    return jsonify({'code': 500, 'message': '分析结果图失败'}), 500
            else:
                # 直接分析LUT文件
                analysis_result = analysis_service.analyze_lut(temp_file_path)
                
                # 删除临时文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                if analysis_result is None:
                    return jsonify({'code': 500, 'message': '分析失败，无法解析LUT文件'}), 500
            
            return jsonify({
                'code': 200,
                'message': '分析成功',
                'data': {
                    'filename': file.filename,
                    'analysis_mode': analysis_mode,
                    'analysis_result': analysis_result
                }
            })
        except Exception as e:
            # 删除临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            error_detail = traceback.format_exc()
            current_app.logger.error(f"分析LUT文件失败: {error_detail}")
            return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"测试分析LUT文件失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch-analyze-interrupt', methods=['POST'])
def interrupt_batch_analyze():
    """中断批量分析任务"""
    try:
        # 查找运行中的任务
        task = LutFileAnalysisTask.query.filter_by(status='running').first()
        
        if not task:
            return jsonify({'code': 400, 'message': '没有运行中的批量分析任务'}), 400
        
        # 设置中断标志
        task.interrupted = True
        # 强制刷新，确保标志被写入数据库
        db.session.flush()
        db.session.commit()
        
        # 再次查询确认标志已设置
        db.session.refresh(task)
        current_app.logger.info(f"批量分析任务 {task.id} 已被标记为中断，interrupted={task.interrupted}")
        
        return jsonify({
            'code': 200,
            'message': '任务中断请求已发送，任务将在处理完当前文件后停止'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"中断批量分析任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

def get_lut_cluster_image_dir():
    """获取LUT聚类分析图片存储目录"""
    base_dir = get_local_image_dir()
    cluster_image_dir = os.path.join(os.path.dirname(base_dir), 'storage', 'lut_cluster_images')
    os.makedirs(cluster_image_dir, exist_ok=True)
    return cluster_image_dir

@bp.route('/cluster', methods=['POST'])
def cluster_lut_files():
    """执行LUT文件聚类分析"""
    try:
        data = request.get_json() or {}
        n_clusters = data.get('n_clusters', 5)  # 默认5个聚类
        metric = data.get('metric', 'lightweight_7d')  # 聚类指标：默认使用轻量7维特征
        algorithm = data.get('algorithm', 'kmeans')  # 聚类算法：默认使用K-Means
        reuse_images = data.get('reuse_images', True)  # 默认复用已生成的图片
        
        if n_clusters < 2:
            return jsonify({'code': 400, 'message': '聚类数必须大于等于2'}), 400
        
        if metric not in ['lightweight_7d', 'image_features', 'image_similarity', 'ssim', 'euclidean']:
            return jsonify({'code': 400, 'message': '不支持的聚类指标，支持的指标：lightweight_7d（轻量7维特征）、image_features（图像特征映射）、image_similarity（图片相似度）、ssim（结构相似性）、euclidean（像素欧氏距离）'}), 400
        
        if algorithm not in ['kmeans', 'hierarchical']:
            return jsonify({'code': 400, 'message': '不支持的聚类算法，支持的算法：kmeans（K-Means）、hierarchical（凝聚式层次聚类）'}), 400
        
        # image_similarity、ssim 和 euclidean 方法只能使用层次聚类（因为它们已经计算了距离矩阵）
        if metric in ['image_similarity', 'ssim', 'euclidean'] and algorithm != 'hierarchical':
            return jsonify({'code': 400, 'message': f'聚类指标"{metric}"只能使用层次聚类算法'}), 400
        
        # 获取所有.cube格式的LUT文件
        lut_files = LutFile.query.filter(
            db.func.lower(LutFile.original_filename).like('%.cube')
        ).all()
        
        if len(lut_files) < n_clusters:
            return jsonify({'code': 400, 'message': f'LUT文件数量({len(lut_files)})少于聚类数({n_clusters})'}), 400
        
        # 提取所有LUT文件的特征
        analysis_service = LutAnalysisService()
        storage_dir = get_lut_storage_dir()
        
        features_list = []
        file_ids = []
        failed_files = []
        
        # 如果是图像特征映射、图片相似度、SSIM或欧氏距离方法，需要找到标准测试图
        standard_image_path = None
        if metric in ['image_features', 'image_similarity', 'ssim', 'euclidean']:
            # __file__ 是 backend/app/api/lut_file.py，需要往上3级到backend目录
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # image_similarity、ssim 和 euclidean 方法优先使用 lut_standard.png
            if metric in ['image_similarity', 'ssim', 'euclidean']:
                # 优先查找lut_standard.png
                standard_image_path = os.path.join(backend_dir, 'lut_standard.png')
                if not os.path.exists(standard_image_path):
                    # 如果不存在，尝试standard.png
                    standard_image_path = os.path.join(backend_dir, 'standard.png')
                    if not os.path.exists(standard_image_path):
                        return jsonify({'code': 400, 'message': '标准测试图不存在，请确保backend目录下有lut_standard.png或standard.png文件'}), 400
            else:  # image_features
                # image_features 方法保持原逻辑：先查找standard.png
                standard_image_path = os.path.join(backend_dir, 'standard.png')
                if not os.path.exists(standard_image_path):
                    # 尝试lut_standard.png
                    standard_image_path = os.path.join(backend_dir, 'lut_standard.png')
                    if not os.path.exists(standard_image_path):
                        return jsonify({'code': 400, 'message': '标准测试图不存在，请确保backend目录下有standard.png或lut_standard.png文件'}), 400
        
        metric_name_map = {
            'lightweight_7d': '轻量7维特征',
            'image_features': '图像特征映射',
            'image_similarity': '图片相似度',
            'ssim': 'SSIM（结构相似性）',
            'euclidean': '像素欧氏距离'
        }
        algorithm_name_map = {
            'kmeans': 'K-Means',
            'hierarchical': '凝聚式层次聚类'
        }
        metric_name = metric_name_map.get(metric, '未知指标')
        algorithm_name = algorithm_name_map.get(algorithm, '未知算法')
        current_app.logger.info(f"开始使用{metric_name}指标和{algorithm_name}算法提取 {len(lut_files)} 个LUT文件的特征")
        
        # 图片相似度方法、SSIM方法和欧氏距离方法需要特殊处理
        file_distances = {}  # 初始化距离字典
        if metric in ['image_similarity', 'ssim', 'euclidean']:
            # 先将所有LUT应用到标准测试图，生成结果图
            from app.services.lut_application_service import LutApplicationService
            
            lut_service = LutApplicationService()
            # 使用固定的存储目录，而不是临时目录，以便复用
            cluster_image_dir = get_lut_cluster_image_dir()
            image_paths = []
            
            for lut_file in lut_files:
                file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
                if not os.path.exists(file_path):
                    failed_files.append({'id': lut_file.id, 'filename': lut_file.original_filename, 'error': '文件不存在'})
                    continue
                
                try:
                    # 生成图片路径（使用固定目录，文件名包含LUT文件ID）
                    output_path = os.path.join(cluster_image_dir, f"lut_cluster_{lut_file.id}.jpg")
                    
                    # 如果启用复用且文件已存在，直接使用
                    if reuse_images and os.path.exists(output_path):
                        current_app.logger.info(f"复用已生成的图片: LUT文件ID={lut_file.id}, 路径={output_path}")
                        image_paths.append(output_path)
                        file_ids.append(lut_file.id)
                    else:
                        # 应用LUT到标准测试图
                        success, error_msg = lut_service.apply_lut_to_image(
                            standard_image_path,
                            file_path,
                            output_path
                        )
                        
                        if success:
                            current_app.logger.info(f"生成新图片: LUT文件ID={lut_file.id}, 路径={output_path}")
                            image_paths.append(output_path)
                            file_ids.append(lut_file.id)
                        else:
                            failed_files.append({'id': lut_file.id, 'filename': lut_file.original_filename, 'error': f'应用LUT失败: {error_msg}'})
                except Exception as e:
                    failed_files.append({'id': lut_file.id, 'filename': lut_file.original_filename, 'error': str(e)})
            
            if len(image_paths) < n_clusters:
                # 如果reuse_images为False，清理生成的图片
                if not reuse_images:
                    for img_path in image_paths:
                        try:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                        except:
                            pass
                return jsonify({
                    'code': 400,
                    'message': f'成功生成图片的LUT文件数量({len(image_paths)})少于聚类数({n_clusters})',
                    'data': {'failed_files': failed_files}
                }), 400
            
            # 计算相似度矩阵或距离矩阵
            try:
                if metric == 'ssim':
                    similarity_matrix = analysis_service.calculate_ssim_similarity_matrix(image_paths)
                    if similarity_matrix is None:
                        # 如果reuse_images为False，清理生成的图片
                        if not reuse_images:
                            for img_path in image_paths:
                                try:
                                    if os.path.exists(img_path):
                                        os.remove(img_path)
                                except:
                                    pass
                        return jsonify({'code': 500, 'message': '计算相似度矩阵失败'}), 500
                    # 将相似度矩阵转换为距离矩阵（1 - 相似度）
                    distance_matrix = 1 - similarity_matrix
                elif metric == 'euclidean':
                    # 计算欧氏距离矩阵
                    distance_matrix = analysis_service.calculate_euclidean_distance_matrix(image_paths)
                    if distance_matrix is None:
                        # 如果reuse_images为False，清理生成的图片
                        if not reuse_images:
                            for img_path in image_paths:
                                try:
                                    if os.path.exists(img_path):
                                        os.remove(img_path)
                                except:
                                    pass
                        return jsonify({'code': 500, 'message': '计算欧氏距离矩阵失败'}), 500
                else:  # image_similarity
                    similarity_matrix = analysis_service.calculate_image_similarity_matrix(image_paths)
                    if similarity_matrix is None:
                        # 如果reuse_images为False，清理生成的图片
                        if not reuse_images:
                            for img_path in image_paths:
                                try:
                                    if os.path.exists(img_path):
                                        os.remove(img_path)
                                except:
                                    pass
                        return jsonify({'code': 500, 'message': '计算相似度矩阵失败'}), 500
                    # 将相似度矩阵转换为距离矩阵（1 - 相似度）
                    distance_matrix = 1 - similarity_matrix
                
                # 使用层次聚类（AgglomerativeClustering）进行聚类
                from sklearn.cluster import AgglomerativeClustering
                
                # 使用预计算的距离矩阵
                clustering = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    linkage='average',
                    metric='precomputed'
                )
                cluster_labels = clustering.fit_predict(distance_matrix)
                
                # 计算每个文件到其所属聚类中心的距离（基于距离矩阵）
                import numpy as np
                for cluster_id in range(n_clusters):
                    cluster_mask = cluster_labels == cluster_id
                    cluster_indices = np.where(cluster_mask)[0]
                    if len(cluster_indices) > 0:
                        # 计算该聚类内所有点到其他点的平均距离，作为到中心的距离
                        for idx in cluster_indices:
                            # 计算该点到聚类内其他所有点的平均距离
                            cluster_distances = distance_matrix[idx, cluster_indices]
                            avg_distance = np.mean(cluster_distances)
                            file_id = file_ids[idx]
                            file_distances[file_id] = float(avg_distance)
                
                # 如果reuse_images为False，清理生成的图片
                if not reuse_images:
                    for img_path in image_paths:
                        try:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                        except:
                            pass
                else:
                    current_app.logger.info(f"保留生成的图片文件以便复用，共 {len(image_paths)} 个文件")
                        
            except Exception as e:
                # 如果reuse_images为False，清理生成的图片
                if not reuse_images:
                    for img_path in image_paths:
                        try:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                        except:
                            pass
                metric_name_display = metric_name_map.get(metric, metric)
                current_app.logger.error(f"{metric_name_display}聚类失败: {e}")
                return jsonify({'code': 500, 'message': f'{metric_name_display}聚类失败: {str(e)}'}), 500
        
        else:
            # 其他方法：提取特征向量
            for lut_file in lut_files:
                file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
                if not os.path.exists(file_path):
                    failed_files.append({'id': lut_file.id, 'filename': lut_file.original_filename, 'error': '文件不存在'})
                    continue
                
                try:
                    if metric == 'lightweight_7d':
                        features = analysis_service.extract_7d_features(file_path)
                    else:  # image_features
                        features = analysis_service.extract_image_features(file_path, standard_image_path)
                    
                    if features is not None:
                        features_list.append(features)
                        file_ids.append(lut_file.id)
                    else:
                        failed_files.append({'id': lut_file.id, 'filename': lut_file.original_filename, 'error': '特征提取失败'})
                except Exception as e:
                    failed_files.append({'id': lut_file.id, 'filename': lut_file.original_filename, 'error': str(e)})
            
            if len(features_list) < n_clusters:
                return jsonify({
                    'code': 400,
                    'message': f'成功提取特征的LUT文件数量({len(features_list)})少于聚类数({n_clusters})',
                    'data': {'failed_files': failed_files}
                }), 400
            
            # 根据选择的算法进行聚类
            try:
                from sklearn.cluster import KMeans, AgglomerativeClustering
                from sklearn.preprocessing import StandardScaler
                from sklearn.metrics import pairwise_distances
                
                # 特征标准化
                scaler = StandardScaler()
                features_scaled = scaler.fit_transform(features_list)
                
                if algorithm == 'kmeans':
                    # K-Means聚类
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
                    cluster_labels = kmeans.fit_predict(features_scaled)
                    # K-Means可以直接获取聚类中心
                    cluster_centers = kmeans.cluster_centers_
                else:  # hierarchical
                    # 凝聚式层次聚类
                    # 计算距离矩阵（欧氏距离）
                    distance_matrix = pairwise_distances(features_scaled, metric='euclidean')
                    
                    clustering = AgglomerativeClustering(
                        n_clusters=n_clusters,
                        linkage='average',
                        metric='precomputed'
                    )
                    cluster_labels = clustering.fit_predict(distance_matrix)
                    # 对于层次聚类，需要计算每个聚类的中心（均值）
                    import numpy as np
                    cluster_centers = {}
                    for cluster_id in range(n_clusters):
                        cluster_mask = cluster_labels == cluster_id
                        if np.any(cluster_mask):
                            cluster_centers[cluster_id] = np.mean(features_scaled[cluster_mask], axis=0)
            except ImportError:
                return jsonify({'code': 500, 'message': 'sklearn库未安装，请安装: pip install scikit-learn'}), 500
            except Exception as e:
                db.session.rollback()
                error_detail = traceback.format_exc()
                current_app.logger.error(f"{algorithm_name}聚类失败: {error_detail}")
                return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
        
        # 计算每个文件到其所属聚类中心的距离（仅对特征向量方法）
        # euclidean 方法使用距离矩阵，不需要计算到中心的距离（已在上面计算）
        if metric not in ['image_similarity', 'ssim', 'euclidean']:
            import numpy as np
            file_distances = {}
            if algorithm == 'kmeans':
                # K-Means：直接使用聚类中心
                for i, (file_id, cluster_id) in enumerate(zip(file_ids, cluster_labels)):
                    center = cluster_centers[int(cluster_id)]
                    distance = np.linalg.norm(features_scaled[i] - center)
                    file_distances[file_id] = float(distance)
            else:
                # 层次聚类：使用计算出的聚类中心
                for i, (file_id, cluster_id) in enumerate(zip(file_ids, cluster_labels)):
                    cluster_id_int = int(cluster_id)
                    if cluster_id_int in cluster_centers:
                        center = cluster_centers[cluster_id_int]
                        distance = np.linalg.norm(features_scaled[i] - center)
                        file_distances[file_id] = float(distance)
                    else:
                        # 如果聚类中心不存在，计算该聚类内所有点的均值作为中心
                        cluster_mask = cluster_labels == cluster_id_int
                        if np.any(cluster_mask):
                            center = np.mean(features_scaled[cluster_mask], axis=0)
                            distance = np.linalg.norm(features_scaled[i] - center)
                            file_distances[file_id] = float(distance)
                        else:
                            file_distances[file_id] = None
        # 对于 image_similarity 和 ssim 方法，距离已在上面计算
        
        # 删除旧的聚类结果
        LutCluster.query.delete()
        db.session.commit()
        
        # 保存聚类结果（包含距离）
        cluster_records = []
        for file_id, cluster_id in zip(file_ids, cluster_labels):
            cluster_record = LutCluster(
                cluster_id=int(cluster_id),
                lut_file_id=file_id,
                distance_to_center=file_distances.get(file_id)
            )
            cluster_records.append(cluster_record)
            db.session.add(cluster_record)
        
        db.session.commit()
        
        # 统计每个聚类的文件数量
        cluster_stats = {}
        for record in cluster_records:
            cluster_id = record.cluster_id
            if cluster_id not in cluster_stats:
                cluster_stats[cluster_id] = 0
            cluster_stats[cluster_id] += 1
        
        current_app.logger.info(f"聚类完成: {len(cluster_records)} 个文件分为 {n_clusters} 个聚类（使用{metric_name}指标和{algorithm_name}算法）")
        
        return jsonify({
            'code': 200,
            'message': '聚类分析完成',
            'data': {
                'n_clusters': n_clusters,
                'metric': metric,
                'metric_name': metric_name,
                'algorithm': algorithm,
                'algorithm_name': algorithm_name,
                'total_files': len(cluster_records),
                'failed_files': failed_files,
                'cluster_stats': cluster_stats
            }
        })
            
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"LUT聚类分析失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/cluster/stats', methods=['GET'])
def get_cluster_stats():
    """获取聚类统计信息"""
    try:
        # 统计每个聚类的文件数量
        from sqlalchemy import func
        
        # 检查表是否存在
        try:
            # 只统计未蒸馏的文件
            stats = db.session.query(
                LutCluster.cluster_id,
                func.count(LutCluster.id).label('file_count')
            ).filter(
                LutCluster.distilled == False
            ).group_by(LutCluster.cluster_id).all()
        except Exception as query_error:
            # 如果查询失败，可能是表不存在或没有数据
            current_app.logger.warning(f"查询聚类统计失败: {query_error}")
            # 返回空结果而不是错误
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'total_clusters': 0,
                    'total_files': 0,
                    'cluster_stats': {}
                }
            })
        
        # 处理查询结果
        cluster_stats = {}
        total_files = 0
        for stat in stats:
            # 兼容不同的访问方式
            cluster_id = stat.cluster_id if hasattr(stat, 'cluster_id') else stat[0]
            file_count = stat.file_count if hasattr(stat, 'file_count') else stat[1]
            cluster_stats[str(cluster_id)] = file_count
            total_files += file_count
        
        total_clusters = len(stats)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_clusters': total_clusters,
                'total_files': total_files,
                'cluster_stats': cluster_stats
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取聚类统计失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/cluster/<int:cluster_id>/files', methods=['GET'])
def get_cluster_files(cluster_id):
    """获取指定聚类的LUT文件列表（按与聚类中心的距离排序）"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        sort_by_distance = request.args.get('sort_by_distance', 'true', type=str).lower() == 'true'  # 默认按距离排序
        
        from sqlalchemy.orm import joinedload
        import numpy as np
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import pairwise_distances
        
        # 查询指定聚类的所有LUT文件（排除已蒸馏的文件）
        all_files = LutFile.query.join(LutCluster).filter(
            LutCluster.cluster_id == cluster_id,
            LutCluster.distilled == False
        ).options(
            joinedload(LutFile.category),
            joinedload(LutFile.tags)
        ).all()
        
        total = len(all_files)
        
        if total == 0:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'list': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'cluster_id': cluster_id
                }
            })
        
        # 如果需要按距离排序，使用数据库中存储的距离
        if sort_by_distance:
            # 使用JOIN查询，按distance_to_center排序
            # MySQL不支持NULLS LAST，使用CASE表达式将NULL值排序到最后
            from sqlalchemy import case, func
            query_with_distance = LutFile.query.join(LutCluster).filter(
                LutCluster.cluster_id == cluster_id,
                LutCluster.distilled == False
            ).options(
                joinedload(LutFile.category),
                joinedload(LutFile.tags)
            ).order_by(
                case(
                    (LutCluster.distance_to_center.is_(None), 1),
                    else_=0
                ),
                LutCluster.distance_to_center.asc()  # NULL值通过CASE表达式排在最后
            )
            
            total = query_with_distance.count()
            files = query_with_distance.offset((page - 1) * page_size).limit(page_size).all()
        else:
            # 不按距离排序，使用原始顺序
            files = all_files[(page - 1) * page_size:page * page_size]
        
        # 构建返回数据
        result_list = []
        for f in files:
            file_dict = f.to_dict()
            # 添加标签信息
            if f.tags:
                tag = f.tags[0]
                file_dict['tag'] = tag.to_dict()
            result_list.append(file_dict)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': result_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'cluster_id': cluster_id
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取聚类文件列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:file_id>/thumbnail', methods=['GET'])
def get_lut_file_thumbnail(file_id):
    """获取LUT文件缩略图"""
    try:
        lut_file = LutFile.query.get_or_404(file_id)
        
        if not lut_file.thumbnail_path:
            return jsonify({'code': 404, 'message': '缩略图不存在'}), 404
        
        # 获取缩略图文件路径
        base_dir = get_local_image_dir()
        thumbnail_path = os.path.join(os.path.dirname(base_dir), 'storage', lut_file.thumbnail_path.replace('/', os.sep))
        
        if not os.path.exists(thumbnail_path):
            return jsonify({'code': 404, 'message': '缩略图文件不存在'}), 404
        
        return send_file(thumbnail_path)
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取LUT文件缩略图失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:file_id>/generate-thumbnail', methods=['POST'])
def generate_thumbnail(file_id):
    """生成LUT文件缩略图"""
    try:
        lut_file = LutFile.query.get_or_404(file_id)
        
        # 检查文件扩展名，目前只支持.cube格式
        if not lut_file.original_filename.lower().endswith('.cube'):
            return jsonify({'code': 400, 'message': '目前只支持.cube格式的LUT文件生成缩略图'}), 400
        
        # 获取文件路径
        storage_dir = get_lut_storage_dir()
        file_path = os.path.join(storage_dir, lut_file.storage_path.replace('/', os.sep))
        
        if not os.path.exists(file_path):
            return jsonify({'code': 404, 'message': '文件不存在'}), 404
        
        # 生成缩略图
        thumbnail_path = generate_lut_thumbnail(file_id, file_path)
        
        if thumbnail_path:
            lut_file.thumbnail_path = thumbnail_path
            db.session.commit()
            return jsonify({
                'code': 200,
                'message': '缩略图生成成功',
                'data': {'thumbnail_path': thumbnail_path}
            })
        else:
            return jsonify({'code': 500, 'message': '缩略图生成失败'}), 500
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"生成LUT文件缩略图失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/cluster/<int:cluster_id>/distill/<int:lut_file_id>', methods=['POST'])
def distill_lut_file(cluster_id, lut_file_id):
    """蒸馏LUT文件（标记为已蒸馏，不再显示在聚类中）"""
    try:
        # 查找聚类记录
        cluster_record = LutCluster.query.filter_by(
            cluster_id=cluster_id,
            lut_file_id=lut_file_id
        ).first()
        
        if not cluster_record:
            return jsonify({'code': 404, 'message': '聚类记录不存在'}), 404
        
        # 标记为已蒸馏
        cluster_record.distilled = True
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '蒸馏成功',
            'data': {'distilled': True}
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"蒸馏LUT文件失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/cluster/snapshot', methods=['POST'])
def save_cluster_snapshot():
    """保存聚类分析快照"""
    try:
        data = request.get_json() or {}
        name = data.get('name', '')
        description = data.get('description', '')
        metric = data.get('metric', 'unknown')
        metric_name = data.get('metric_name', '未知')
        algorithm = data.get('algorithm', 'unknown')
        algorithm_name = data.get('algorithm_name', '未知')
        
        if not name:
            return jsonify({'code': 400, 'message': '快照名称不能为空'}), 400
        
        # 获取当前聚类统计信息
        from sqlalchemy import func
        stats = db.session.query(
            LutCluster.cluster_id,
            func.count(LutCluster.id).label('file_count')
        ).filter(
            LutCluster.distilled == False
        ).group_by(LutCluster.cluster_id).all()
        
        if not stats:
            return jsonify({'code': 400, 'message': '没有可保存的聚类数据'}), 400
        
        # 获取每个聚类的详细信息
        cluster_data = {}
        for stat in stats:
            cluster_id = stat.cluster_id if hasattr(stat, 'cluster_id') else stat[0]
            file_count = stat.file_count if hasattr(stat, 'file_count') else stat[1]
            
            # 获取该聚类的文件列表（未蒸馏的）
            files = LutFile.query.join(LutCluster).filter(
                LutCluster.cluster_id == cluster_id,
                LutCluster.distilled == False
            ).all()
            
            cluster_data[str(cluster_id)] = {
                'file_count': file_count,
                'files': [f.to_dict() for f in files]
            }
        
        # 创建快照记录
        snapshot = LutClusterSnapshot(
            name=name,
            description=description,
            metric=metric,
            metric_name=metric_name,
            algorithm=algorithm,
            algorithm_name=algorithm_name,
            n_clusters=len(stats),
            cluster_data_json=json.dumps(cluster_data, ensure_ascii=False)
        )
        
        db.session.add(snapshot)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '快照保存成功',
            'data': snapshot.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"保存聚类快照失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/cluster/snapshots', methods=['GET'])
def get_cluster_snapshots():
    """获取聚类快照列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        query = LutClusterSnapshot.query.order_by(LutClusterSnapshot.created_at.desc())
        total = query.count()
        snapshots = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [s.to_dict() for s in snapshots],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取聚类快照列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/cluster/snapshot/<int:snapshot_id>', methods=['GET'])
def get_cluster_snapshot(snapshot_id):
    """获取聚类快照详情"""
    try:
        snapshot = LutClusterSnapshot.query.get_or_404(snapshot_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': snapshot.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取聚类快照详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
