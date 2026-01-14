# -*- coding: utf-8 -*-
"""
语义搜索API
"""
from flask import Blueprint, request, jsonify, current_app, send_file
from app.database import db
from app.models.image import Image
from app.models.semantic_search import SemanticSearchImage
from app.models.image_recycle import ImageRecycle
from app.services.semantic_search_service import get_semantic_search_service
from app.utils.config_manager import get_local_image_dir
from threading import Thread
import traceback
import os
from datetime import datetime

bp = Blueprint('semantic_search', __name__)

# 编码任务状态
_encoding_task_status = {
    'running': False,
    'total': 0,
    'processed': 0,
    'success': 0,
    'failed': 0,
    'current_image_id': None,
    'error_message': None
}

@bp.route('/stats', methods=['GET'])
def get_stats():
    """获取语义搜索统计信息"""
    try:
        service = get_semantic_search_service()
        
        # 尝试初始化服务，如果失败则返回友好的错误信息
        try:
            service.initialize()
            collection_stats = service.get_collection_stats()
        except Exception as e:
            error_detail = traceback.format_exc()
            current_app.logger.error(f"初始化语义搜索服务失败: {error_detail}")
            # 检查是否是 FAISS 模块缺失的错误
            error_msg = str(e)
            if "faiss" in error_msg.lower() or "no module named 'faiss'" in error_msg.lower():
                error_hint = "请安装 FAISS 包: pip install faiss-cpu 或 pip install faiss-gpu"
            elif "clip" in error_msg.lower():
                error_hint = "请安装 CLIP 包: pip install open-clip-torch"
            else:
                error_hint = str(e)
            
            collection_stats = {
                'total_images': 0,
                'total_vectors': 0,
                'collection_name': service.collection_name,
                'dimension': service.dimension,
                'error': error_hint
            }
        
        # 统计数据库中的编码状态
        total_images = Image.query.filter_by(status='active').count()
        encoded_count = SemanticSearchImage.query.filter_by(encoded=True).count()
        not_encoded_count = total_images - encoded_count
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_images': total_images,
                'encoded_count': encoded_count,
                'not_encoded_count': not_encoded_count,
                'collection_stats': collection_stats,
                'encoding_task': _encoding_task_status
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取统计信息失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/search/text', methods=['POST'])
def search_by_text():
    """文本搜索图片"""
    try:
        data = request.get_json() or {}
        query_text = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        
        if not query_text:
            return jsonify({'code': 400, 'message': '查询文本不能为空'}), 400
        
        service = get_semantic_search_service()
        service.initialize()
        
        # 执行搜索
        results = service.search_by_text(query_text, top_k=top_k)
        
        # 获取图片详情
        image_ids = [r['image_id'] for r in results]
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        image_map = {img.id: img for img in images}
        
        # 构建返回结果
        search_results = []
        for result in results:
            image_id = result['image_id']
            if image_id in image_map:
                image = image_map[image_id]
                search_results.append({
                    'image_id': image_id,
                    'score': result['score'],
                    'distance': result['distance'],
                    'image': image.to_dict()
                })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'query': query_text,
                'results': search_results,
                'total': len(search_results)
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"文本搜索失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/search/image', methods=['POST'])
def search_by_image():
    """图片搜索图片"""
    try:
        if 'image' not in request.files:
            return jsonify({'code': 400, 'message': '请上传查询图片'}), 400
        
        file = request.files['image']
        top_k = request.form.get('top_k', 10, type=int)
        
        if file.filename == '':
            return jsonify({'code': 400, 'message': '请上传有效的图片文件'}), 400
        
        # 保存临时文件
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"search_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file.save(temp_path)
        
        try:
            service = get_semantic_search_service()
            service.initialize()
            
            # 执行搜索
            results = service.search_by_image(temp_path, top_k=top_k)
            
            # 获取图片详情
            image_ids = [r['image_id'] for r in results]
            images = Image.query.filter(Image.id.in_(image_ids)).all()
            image_map = {img.id: img for img in images}
            
            # 构建返回结果
            search_results = []
            for result in results:
                image_id = result['image_id']
                if image_id in image_map:
                    image = image_map[image_id]
                    search_results.append({
                        'image_id': image_id,
                        'score': result['score'],
                        'distance': result['distance'],
                        'image': image.to_dict()
                    })
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'results': search_results,
                    'total': len(search_results)
                }
            })
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"图片搜索失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

def _encode_images_task():
    """后台编码任务"""
    global _encoding_task_status
    
    # 在后台线程中需要创建 Flask 应用上下文
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            _encoding_task_status['running'] = True
            _encoding_task_status['processed'] = 0
            _encoding_task_status['success'] = 0
            _encoding_task_status['failed'] = 0
            _encoding_task_status['error_message'] = None
            
            app.logger.info("=" * 60)
            app.logger.info("语义编码任务开始")
            app.logger.info("=" * 60)
            
            service = get_semantic_search_service()
            service.initialize()
            
            # 获取所有未编码的图片
            encoded_image_ids = [row[0] for row in db.session.query(SemanticSearchImage.image_id).filter_by(encoded=True).all()]
            if encoded_image_ids:
                images = Image.query.filter(
                    Image.status == 'active',
                    ~Image.id.in_(encoded_image_ids)
                ).all()
            else:
                images = Image.query.filter_by(status='active').all()
            
            _encoding_task_status['total'] = len(images)
            app.logger.info(f"开始编码 {len(images)} 张图片")
            
            image_dir = get_local_image_dir()
            
            for image in images:
                _encoding_task_status['current_image_id'] = image.id
                _encoding_task_status['processed'] += 1
                
                try:
                    # 构建图片路径
                    image_path = os.path.join(image_dir, image.storage_path)
                    if not os.path.exists(image_path):
                        app.logger.warning(f"图片文件不存在: {image_path} (image_id={image.id})")
                        _encoding_task_status['failed'] += 1
                        continue
                    
                    # 编码图片
                    app.logger.debug(f"正在编码图片 image_id={image.id}, path={image_path}")
                    vector = service.encode_image(image_path)
                    
                    # 添加到FAISS索引
                    vector_id = service.add_image_vector(image.id, vector)
                    
                    # 更新数据库记录
                    semantic_record = SemanticSearchImage.query.filter_by(image_id=image.id).first()
                    if semantic_record:
                        semantic_record.encoded = True
                        semantic_record.vector_id = str(vector_id) if vector_id else None
                        semantic_record.encoded_at = datetime.now()
                    else:
                        semantic_record = SemanticSearchImage(
                            image_id=image.id,
                            vector_id=str(vector_id) if vector_id else None,
                            encoded=True,
                            encoded_at=datetime.now()
                        )
                        db.session.add(semantic_record)
                    
                    db.session.commit()
                    _encoding_task_status['success'] += 1
                    
                    # 每10张图片记录一次进度（而不是100张）
                    if _encoding_task_status['processed'] % 10 == 0:
                        app.logger.info(f"编码进度: {_encoding_task_status['processed']}/{_encoding_task_status['total']} "
                                      f"(成功: {_encoding_task_status['success']}, 失败: {_encoding_task_status['failed']})")
                    
                except Exception as e:
                    _encoding_task_status['failed'] += 1
                    error_detail = traceback.format_exc()
                    app.logger.error(f"编码图片失败 image_id={image.id}: {str(e)}")
                    app.logger.debug(f"错误详情: {error_detail}")
                    db.session.rollback()
                    continue
            
            app.logger.info("=" * 60)
            app.logger.info(f"编码任务完成: 总计 {_encoding_task_status['total']} 张, "
                          f"成功 {_encoding_task_status['success']} 张, "
                          f"失败 {_encoding_task_status['failed']} 张")
            app.logger.info("=" * 60)
            
        except Exception as e:
            error_detail = traceback.format_exc()
            _encoding_task_status['error_message'] = str(e)
            app.logger.error(f"编码任务失败: {error_detail}")
        finally:
            _encoding_task_status['running'] = False
            _encoding_task_status['current_image_id'] = None
            app.logger.info("语义编码任务结束")

@bp.route('/encode/start', methods=['POST'])
def start_encoding():
    """启动图片编码任务"""
    try:
        global _encoding_task_status
        
        if _encoding_task_status['running']:
            return jsonify({
                'code': 400,
                'message': '编码任务正在运行中'
            }), 400
        
        # 在后台线程中运行
        thread = Thread(target=_encode_images_task, daemon=True)
        thread.start()
        
        return jsonify({
            'code': 200,
            'message': '编码任务已启动'
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动编码任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/encode/status', methods=['GET'])
def get_encoding_status():
    """获取编码任务状态"""
    try:
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': _encoding_task_status
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取编码任务状态失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/images/<int:image_id>/recycle', methods=['POST'])
def recycle_image(image_id):
    """将语义搜索结果中的图片移动到回收站（人工删除）"""
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
        
        # 删除语义搜索索引中的记录
        semantic_search_image = SemanticSearchImage.query.filter_by(image_id=image_id).first()
        if semantic_search_image:
            # 从FAISS索引中删除
            try:
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
