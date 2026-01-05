# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.tagging_task import TaggingTask
import traceback
import json
from datetime import datetime

bp = Blueprint('tagging_task', __name__)

@bp.route('', methods=['GET'])
def get_task_list():
    """获取数据打标任务列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        status = request.args.get('status', type=str)
        
        query = TaggingTask.query
        
        if keyword:
            query = query.filter(TaggingTask.name.like(f'%{keyword}%'))
        
        if status:
            query = query.filter(TaggingTask.status == status)
        
        total = query.count()
        tasks = query.order_by(TaggingTask.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [task.to_dict() for task in tasks],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取数据打标任务列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>', methods=['GET'])
def get_task_detail(task_id):
    """获取数据打标任务详情"""
    try:
        task = TaggingTask.query.get_or_404(task_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取数据打标任务详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_task():
    """创建数据打标任务"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '任务名称不能为空'}), 400
        
        # 处理打标特征和关键字
        tagging_features = data.get('tagging_features', [])
        filter_keywords = data.get('filter_keywords', [])
        
        # 创建任务（status、total_count、processed_count 由系统自动管理）
        task = TaggingTask(
            name=data['name'],
            description=data.get('description'),
            tagging_features=json.dumps(tagging_features, ensure_ascii=False) if tagging_features else None,
            filter_keywords=json.dumps(filter_keywords, ensure_ascii=False) if filter_keywords else None,
            status='pending',
            total_count=0,
            processed_count=0,
            note=data.get('note')
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"创建数据打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新数据打标任务"""
    try:
        task = TaggingTask.query.get_or_404(task_id)
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '任务名称不能为空'}), 400
        
        # 只有 pending 或 failed 状态的任务可以修改
        if task.status not in ['pending', 'failed']:
            return jsonify({'code': 400, 'message': f'任务状态为 {task.status}，无法修改'}), 400
        
        # 更新字段
        task.name = data['name']
        task.description = data.get('description')
        
        # 处理打标特征和关键字
        tagging_features = data.get('tagging_features', [])
        filter_keywords = data.get('filter_keywords', [])
        task.tagging_features = json.dumps(tagging_features, ensure_ascii=False) if tagging_features else None
        task.filter_keywords = json.dumps(filter_keywords, ensure_ascii=False) if filter_keywords else None
        
        task.note = data.get('note')
        task.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新数据打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除数据打标任务"""
    try:
        task = TaggingTask.query.get_or_404(task_id)
        
        # 只有 pending 或 failed 状态的任务可以删除
        if task.status not in ['pending', 'failed', 'completed']:
            return jsonify({'code': 400, 'message': f'任务状态为 {task.status}，无法删除'}), 400
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除数据打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch', methods=['DELETE'])
def batch_delete_tasks():
    """批量删除数据打标任务"""
    try:
        data = request.get_json()
        task_ids = data.get('ids', [])
        
        if not task_ids:
            return jsonify({'code': 400, 'message': '请选择要删除的任务'}), 400
        
        tasks = TaggingTask.query.filter(TaggingTask.id.in_(task_ids)).all()
        
        # 检查任务状态
        for task in tasks:
            if task.status not in ['pending', 'failed', 'completed']:
                return jsonify({'code': 400, 'message': f'任务 {task.name} 状态为 {task.status}，无法删除'}), 400
        
        for task in tasks:
            db.session.delete(task)
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功删除 {len(tasks)} 个任务'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量删除数据打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>/execute', methods=['POST'])
def execute_task(task_id):
    """执行打标任务"""
    try:
        # 检查任务是否存在
        task = TaggingTask.query.get_or_404(task_id)
        
        # 检查是否有需求关联，如果有，检查前置任务是否完成
        try:
            from app.api.requirement import check_prerequisite_tasks
            is_ok, error_msg = check_prerequisite_tasks('tagging', task_id)
            if not is_ok:
                return jsonify({'code': 400, 'message': error_msg}), 400
        except Exception as e:
            current_app.logger.warning(f"检查前置任务失败: {e}")
        
        # 检查任务状态
        if task.status == 'running':
            return jsonify({
                'code': 400,
                'message': '任务正在执行中，请勿重复执行'
            }), 400
        
        if task.status == 'completed':
            return jsonify({
                'code': 400,
                'message': '任务已完成，如需重新执行请先重置任务状态'
            }), 400
        
        # 如果任务是被中断的，允许重启（从上次中断的位置继续）
        if task.status == 'interrupted':
            # 重启中断的任务，保持已处理的进度
            pass
        
        # 导入服务（避免循环导入）
        from app.services.batch_tagging_service import BatchTaggingService
        
        # 执行任务（在后台线程中执行，避免阻塞HTTP请求）
        import threading
        
        def run_tagging():
            """在后台线程中执行打标任务"""
            try:
                from app import create_app
                app_instance = create_app()
                with app_instance.app_context():
                    tagging_service = BatchTaggingService()
                    result = tagging_service.execute_tagging_task(task_id)
                    if result['success']:
                        current_app.logger.info(f"打标任务执行成功 {task_id}: {result.get('stats', {})}")
                    else:
                        current_app.logger.error(f"打标任务执行失败 {task_id}: {result.get('message', '未知错误')}")
            except Exception as e:
                current_app.logger.error(f"后台执行打标任务异常 {task_id}: {str(e)}", exc_info=True)
        
        # 启动后台线程
        thread = threading.Thread(target=run_tagging, daemon=True)
        thread.start()
        
        # 立即返回响应
        return jsonify({
            'code': 200,
            'message': '任务已开始执行',
            'data': task.to_dict()
        })
        
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"执行打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>/interrupt', methods=['POST'])
def interrupt_task(task_id):
    """中断打标任务"""
    try:
        # 检查任务是否存在
        task = TaggingTask.query.get_or_404(task_id)
        
        # 只有running状态的任务可以中断
        if task.status != 'running':
            return jsonify({
                'code': 400,
                'message': f'任务状态为 {task.status}，无法中断'
            }), 400
        
        # 更新任务状态为中断
        task.status = 'interrupted'
        task.finished_at = datetime.now()
        task.last_error = '任务被用户中断'
        
        db.session.commit()
        
        current_app.logger.info(f"打标任务已中断: task_id={task_id}, name={task.name}, processed_count={task.processed_count}")
        
        return jsonify({
            'code': 200,
            'message': '任务已中断',
            'data': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"中断打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>/reset', methods=['POST'])
def reset_task(task_id):
    """重置打标任务"""
    try:
        # 检查任务是否存在
        task = TaggingTask.query.get_or_404(task_id)
        
        # 检查任务状态，只有completed、failed或interrupted状态的任务才能重置
        if task.status == 'running':
            return jsonify({
                'code': 400,
                'message': '任务正在执行中，无法重置'
            }), 400
        
        # 重置任务状态
        task.status = 'pending'
        task.processed_count = 0
        task.total_count = 0
        task.last_error = None
        task.started_at = None
        task.finished_at = None
        
        db.session.commit()
        
        current_app.logger.info(f"打标任务已重置: task_id={task_id}, name={task.name}")
        
        return jsonify({
            'code': 200,
            'message': '任务重置成功',
            'data': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"重置打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>/copy', methods=['POST'])
def copy_task(task_id):
    """复制打标任务"""
    try:
        # 获取源任务
        source_task = TaggingTask.query.get_or_404(task_id)
        
        # 生成新任务名称（添加"副本"后缀）
        new_name = f"{source_task.name}_副本"
        # 如果名称已存在，添加序号
        counter = 1
        while TaggingTask.query.filter_by(name=new_name).first():
            counter += 1
            new_name = f"{source_task.name}_副本{counter}"
        
        # 创建新任务（复制所有配置，但重置状态和进度）
        new_task = TaggingTask(
            name=new_name,
            description=source_task.description,
            tagging_features=source_task.tagging_features,  # 直接复制JSON字符串
            filter_keywords=source_task.filter_keywords,  # 直接复制JSON字符串
            status='pending',
            total_count=0,
            processed_count=0,
            note=source_task.note,
            last_error=None,
            started_at=None,
            finished_at=None
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        current_app.logger.info(f"打标任务已复制: source_task_id={task_id}, new_task_id={new_task.id}, name={new_task.name}")
        
        return jsonify({
            'code': 200,
            'message': '任务复制成功',
            'data': new_task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"复制打标任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

