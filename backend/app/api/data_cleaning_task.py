from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.data_cleaning_task import DataCleaningTask
import traceback
import json
from datetime import datetime

bp = Blueprint('data_cleaning_task', __name__)

@bp.route('', methods=['GET'])
def get_task_list():
    """获取数据清洗任务列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        status = request.args.get('status', type=str)
        
        query = DataCleaningTask.query
        
        if keyword:
            query = query.filter(DataCleaningTask.name.like(f'%{keyword}%'))
        
        if status:
            query = query.filter(DataCleaningTask.status == status)
        
        total = query.count()
        tasks = query.order_by(DataCleaningTask.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
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
        current_app.logger.error(f"获取数据清洗任务列表失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>', methods=['GET'])
def get_task_detail(task_id):
    """获取数据清洗任务详情"""
    try:
        task = DataCleaningTask.query.get_or_404(task_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取数据清洗任务详情失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_task():
    """创建数据清洗任务"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '任务名称不能为空'}), 400
        
        # 处理筛选特征和关键字
        filter_features = data.get('filter_features', [])
        filter_keywords = data.get('filter_keywords', [])
        
        # 创建任务（status 和 processed_count 由系统自动管理，不从前端接收）
        task = DataCleaningTask(
            name=data['name'],
            filter_features=json.dumps(filter_features, ensure_ascii=False) if filter_features else None,
            filter_keywords=json.dumps(filter_keywords, ensure_ascii=False) if filter_keywords else None,
            status='pending',  # 默认状态为 pending
            processed_count=0,  # 默认处理总数为 0
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
        current_app.logger.error(f"创建数据清洗任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新数据清洗任务"""
    try:
        task = DataCleaningTask.query.get_or_404(task_id)
        data = request.get_json()
        
        # 更新字段（status 和 processed_count 由系统自动管理，不从前端接收）
        if 'name' in data:
            task.name = data['name']
        if 'filter_features' in data:
            filter_features = data['filter_features']
            task.filter_features = json.dumps(filter_features, ensure_ascii=False) if filter_features else None
        if 'filter_keywords' in data:
            filter_keywords = data['filter_keywords']
            task.filter_keywords = json.dumps(filter_keywords, ensure_ascii=False) if filter_keywords else None
        # status 和 processed_count 不从前端更新，由系统自动管理
        if 'note' in data:
            task.note = data['note']
        # last_error 通常由系统自动设置，但保留更新能力
        if 'last_error' in data:
            task.last_error = data['last_error']
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新数据清洗任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除数据清洗任务"""
    try:
        task = DataCleaningTask.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"删除数据清洗任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/batch', methods=['DELETE'])
def batch_delete_tasks():
    """批量删除数据清洗任务"""
    try:
        data = request.get_json()
        task_ids = data.get('ids', [])
        
        if not task_ids:
            return jsonify({'code': 400, 'message': '请选择要删除的任务'}), 400
        
        deleted_count = DataCleaningTask.query.filter(DataCleaningTask.id.in_(task_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'成功删除 {deleted_count} 个任务'
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"批量删除数据清洗任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>/execute', methods=['POST'])
def execute_task(task_id):
    """执行数据清洗任务"""
    try:
        # 检查任务是否存在
        task = DataCleaningTask.query.get_or_404(task_id)
        
        # 检查是否有需求关联，如果有，检查前置任务是否完成
        try:
            from app.api.requirement import check_prerequisite_tasks
            is_ok, error_msg = check_prerequisite_tasks('cleaning', task_id)
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
        
        # 导入服务（避免循环导入）
        from app.services.data_cleaning_service import DataCleaningService
        
        # 执行任务（在后台线程中执行，避免阻塞HTTP请求）
        import threading
        
        def run_cleaning():
            """在后台线程中执行清洗任务"""
            try:
                from app import create_app
                app_instance = create_app()
                with app_instance.app_context():
                    cleaning_service = DataCleaningService()
                    result = cleaning_service.execute_cleaning_task(task_id)
                    if result['success']:
                        current_app.logger.info(f"清洗任务执行成功 {task_id}: {result['stats']}")
                    else:
                        current_app.logger.error(f"清洗任务执行失败 {task_id}: {result['message']}")
            except Exception as e:
                current_app.logger.error(f"后台执行清洗任务异常 {task_id}: {str(e)}", exc_info=True)
        
        # 启动后台线程
        thread = threading.Thread(target=run_cleaning, daemon=True)
        thread.start()
        
        # 立即返回响应
        return jsonify({
            'code': 200,
            'message': '清洗任务已启动，正在后台执行',
            'data': {
                'task_id': task_id,
                'task_name': task.name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"启动清洗任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>/reset', methods=['POST'])
def reset_task(task_id):
    """重置数据清洗任务（包括运行中的任务）"""
    try:
        # 检查任务是否存在
        task = DataCleaningTask.query.get_or_404(task_id)
        
        # 如果任务正在运行，先标记为失败（后台线程会检测到状态变化）
        was_running = task.status == 'running'
        if was_running:
            current_app.logger.warning(f"重置运行中的任务: task_id={task_id}, name={task.name}")
        
        # 重置任务状态
        task.status = 'pending'
        task.processed_count = 0
        task.total_count = 0
        task.last_error = None
        task.started_at = None
        task.finished_at = None
        
        db.session.commit()
        
        if was_running:
            current_app.logger.info(f"运行中的任务已重置: task_id={task_id}, name={task.name}，后台线程会在下次检查状态时停止")
        else:
            current_app.logger.info(f"任务已重置: task_id={task_id}, name={task.name}")
        
        return jsonify({
            'code': 200,
            'message': '任务重置成功' + ('（运行中的任务已停止）' if was_running else ''),
            'data': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"重置任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

