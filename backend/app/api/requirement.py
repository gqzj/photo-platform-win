from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.requirement import Requirement
from app.models.requirement_task import RequirementTask
from app.models.crawler_task import CrawlerTask
from app.models.data_cleaning_task import DataCleaningTask
from app.models.tagging_task import TaggingTask
from app.models.sample_set import SampleSet, SampleSetFeature
from datetime import datetime
import json
import traceback
import logging

bp = Blueprint('requirement', __name__)
logger = logging.getLogger(__name__)

@bp.route('', methods=['GET'])
def get_requirement_list():
    """获取需求列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        status = request.args.get('status', type=str)
        requester = request.args.get('requester', type=str)
        keyword = request.args.get('keyword', type=str)
        
        query = Requirement.query
        
        if status:
            query = query.filter(Requirement.status == status)
        if requester:
            query = query.filter(Requirement.requester.like(f'%{requester}%'))
        if keyword:
            query = query.filter(Requirement.name.like(f'%{keyword}%'))
        
        total = query.count()
        requirements = query.order_by(Requirement.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [req.to_dict() for req in requirements],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Error in get_requirement_list: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>', methods=['GET'])
def get_requirement_detail(requirement_id):
    """获取需求详情"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': requirement.to_dict()
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Error in get_requirement_detail: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('', methods=['POST'])
def create_requirement():
    """创建需求"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '需求名称为必填项'}), 400
        
        # 处理JSON字段
        keywords_json = None
        if data.get('keywords'):
            keywords_json = json.dumps(data['keywords'], ensure_ascii=False) if isinstance(data['keywords'], list) else data['keywords']
        
        cleaning_features_json = None
        if data.get('cleaning_features'):
            cleaning_features_json = json.dumps(data['cleaning_features'], ensure_ascii=False) if not isinstance(data['cleaning_features'], str) else data['cleaning_features']
        
        tagging_features_json = None
        if data.get('tagging_features'):
            tagging_features_json = json.dumps(data['tagging_features'], ensure_ascii=False) if isinstance(data['tagging_features'], list) else data['tagging_features']
        
        sample_set_features_json = None
        if data.get('sample_set_features'):
            sample_set_features_json = json.dumps(data['sample_set_features'], ensure_ascii=False) if not isinstance(data['sample_set_features'], str) else data['sample_set_features']
        
        requirement = Requirement(
            name=data['name'],
            requester=data.get('requester', ''),
            keywords_json=keywords_json,
            cookie_id=data.get('cookie_id'),
            cleaning_features_json=cleaning_features_json,
            tagging_features_json=tagging_features_json,
            sample_set_features_json=sample_set_features_json,
            status=data.get('status', 'pending'),
            note=data.get('note', ''),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(requirement)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': requirement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"Error in create_requirement: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>', methods=['PUT'])
def update_requirement(requirement_id):
    """更新需求"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        data = request.get_json()
        
        if 'name' in data:
            requirement.name = data['name']
        if 'requester' in data:
            requirement.requester = data['requester']
        if 'cookie_id' in data:
            requirement.cookie_id = data['cookie_id'] if data['cookie_id'] else None
        if 'status' in data:
            requirement.status = data['status']
        if 'note' in data:
            requirement.note = data['note']
        
        # 处理JSON字段
        if 'keywords' in data:
            if data['keywords']:
                requirement.keywords_json = json.dumps(data['keywords'], ensure_ascii=False) if isinstance(data['keywords'], list) else data['keywords']
            else:
                requirement.keywords_json = None
        
        if 'cleaning_features' in data:
            if data['cleaning_features']:
                requirement.cleaning_features_json = json.dumps(data['cleaning_features'], ensure_ascii=False) if not isinstance(data['cleaning_features'], str) else data['cleaning_features']
            else:
                requirement.cleaning_features_json = None
        
        if 'tagging_features' in data:
            if data['tagging_features']:
                requirement.tagging_features_json = json.dumps(data['tagging_features'], ensure_ascii=False) if isinstance(data['tagging_features'], list) else data['tagging_features']
            else:
                requirement.tagging_features_json = None
        
        if 'sample_set_features' in data:
            if data['sample_set_features']:
                requirement.sample_set_features_json = json.dumps(data['sample_set_features'], ensure_ascii=False) if not isinstance(data['sample_set_features'], str) else data['sample_set_features']
            else:
                requirement.sample_set_features_json = None
        
        requirement.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': requirement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"Error in update_requirement: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>', methods=['DELETE'])
def delete_requirement(requirement_id):
    """删除需求"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        
        # 只允许删除待处理状态的需求
        if requirement.status != 'pending':
            return jsonify({
                'code': 400,
                'message': f'只有待处理状态的需求可以删除，当前状态为：{requirement.status}'
            }), 400
        
        db.session.delete(requirement)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"Error in delete_requirement: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>/start', methods=['POST'])
def start_requirement(requirement_id):
    """启动需求，自动生成关联任务"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        
        # 检查需求状态
        if requirement.status == 'active':
            return jsonify({
                'code': 400,
                'message': '需求已启动，请勿重复启动'
            }), 400
        
        if requirement.status == 'completed':
            return jsonify({
                'code': 400,
                'message': '需求已完成，无法重新启动'
            }), 400
        
        # 检查是否已有任务关联
        existing_tasks = RequirementTask.query.filter_by(requirement_id=requirement_id).count()
        if existing_tasks > 0:
            return jsonify({
                'code': 400,
                'message': '需求已有关联任务，请先删除后重新启动'
            }), 400
        
        # 解析需求配置
        keywords = []
        if requirement.keywords_json:
            try:
                keywords = json.loads(requirement.keywords_json) if isinstance(requirement.keywords_json, str) else requirement.keywords_json
            except:
                pass
        
        cleaning_features = []
        if requirement.cleaning_features_json:
            try:
                cleaning_features = json.loads(requirement.cleaning_features_json) if isinstance(requirement.cleaning_features_json, str) else requirement.cleaning_features_json
            except:
                pass
        
        tagging_features = []
        if requirement.tagging_features_json:
            try:
                tagging_features = json.loads(requirement.tagging_features_json) if isinstance(requirement.tagging_features_json, str) else requirement.tagging_features_json
            except:
                pass
        
        sample_set_features = []
        if requirement.sample_set_features_json:
            try:
                sample_set_features = json.loads(requirement.sample_set_features_json) if isinstance(requirement.sample_set_features_json, str) else requirement.sample_set_features_json
            except:
                pass
        
        # 创建任务列表
        tasks_created = []
        task_order = 1
        
        # 1. 创建抓取任务（如果有关键字）
        crawler_task_id = None
        if keywords:
            crawler_task = CrawlerTask(
                name=f"{requirement.name}-抓取任务",
                platform='xiaohongshu',
                task_type='keyword',
                target_url='',  # 关键字类型任务不需要target_url，设置为空字符串
                cookie_id=requirement.cookie_id,  # 使用需求中指定的账号
                keywords_json=json.dumps(keywords, ensure_ascii=False),
                status='pending',
                note=f'需求ID: {requirement_id}'
            )
            db.session.add(crawler_task)
            db.session.flush()
            crawler_task_id = crawler_task.id
            
            # 创建需求任务关联
            req_task = RequirementTask(
                requirement_id=requirement_id,
                task_type='crawler',
                task_id=crawler_task_id,
                task_order=task_order,
                status='pending'
            )
            db.session.add(req_task)
            tasks_created.append({
                'type': 'crawler',
                'id': crawler_task_id,
                'order': task_order
            })
            task_order += 1
        
        # 2. 创建数据清洗任务（如果有清洗特征）
        cleaning_task_id = None
        if cleaning_features:
            cleaning_task = DataCleaningTask(
                name=f"{requirement.name}-清洗任务",
                filter_features=json.dumps(cleaning_features, ensure_ascii=False),
                filter_keywords=json.dumps(keywords, ensure_ascii=False) if keywords else None,
                status='pending',
                note=f'需求ID: {requirement_id}'
            )
            db.session.add(cleaning_task)
            db.session.flush()
            cleaning_task_id = cleaning_task.id
            
            # 创建需求任务关联
            req_task = RequirementTask(
                requirement_id=requirement_id,
                task_type='cleaning',
                task_id=cleaning_task_id,
                task_order=task_order,
                status='pending'
            )
            db.session.add(req_task)
            tasks_created.append({
                'type': 'cleaning',
                'id': cleaning_task_id,
                'order': task_order
            })
            task_order += 1
        
        # 3. 创建数据打标任务（如果有打标特征）
        tagging_task_id = None
        if tagging_features:
            tagging_task = TaggingTask(
                name=f"{requirement.name}-打标任务",
                description=f'需求ID: {requirement_id}',
                tagging_features=json.dumps(tagging_features, ensure_ascii=False),
                filter_keywords=json.dumps(keywords, ensure_ascii=False) if keywords else None,
                status='pending',
                note=f'需求ID: {requirement_id}'
            )
            db.session.add(tagging_task)
            db.session.flush()
            tagging_task_id = tagging_task.id
            
            # 创建需求任务关联
            req_task = RequirementTask(
                requirement_id=requirement_id,
                task_type='tagging',
                task_id=tagging_task_id,
                task_order=task_order,
                status='pending'
            )
            db.session.add(req_task)
            tasks_created.append({
                'type': 'tagging',
                'id': tagging_task_id,
                'order': task_order
            })
            task_order += 1
        
        # 4. 创建样本集（如果有样本集特征）
        sample_set_id = None
        if sample_set_features:
            sample_set = SampleSet(
                name=f"{requirement.name}-样本集",
                description=f'需求ID: {requirement_id}',
                status='active'
            )
            db.session.add(sample_set)
            db.session.flush()
            sample_set_id = sample_set.id
            
            # 添加样本集特征
            for feature_data in sample_set_features:
                feature_id = feature_data.get('feature_id')
                feature_name = feature_data.get('feature_name', '')
                value_range = feature_data.get('value_range', [])
                
                if feature_id:
                    # 获取特征信息
                    from app.models.feature import Feature
                    feature = Feature.query.get(feature_id)
                    if feature:
                        feature_name = feature.name
                    
                    sample_set_feature = SampleSetFeature(
                        sample_set_id=sample_set.id,
                        feature_id=feature_id,
                        feature_name=feature_name,
                        value_range=json.dumps(value_range, ensure_ascii=False) if value_range else None,
                        value_type='enum'
                    )
                    db.session.add(sample_set_feature)
            
            # 创建需求任务关联
            req_task = RequirementTask(
                requirement_id=requirement_id,
                task_type='sample_set',
                task_id=sample_set_id,
                task_order=task_order,
                status='pending'
            )
            db.session.add(req_task)
            tasks_created.append({
                'type': 'sample_set',
                'id': sample_set_id,
                'order': task_order
            })
        
        # 初始化进度信息
        progress = {
            'total_tasks': len(tasks_created),
            'completed_tasks': 0,
            'current_task_order': 1,
            'tasks': []
        }
        for task_info in tasks_created:
            progress['tasks'].append({
                'type': task_info['type'],
                'id': task_info['id'],
                'order': task_info['order'],
                'status': 'pending'
            })
        
        requirement.status = 'active'
        requirement.progress_json = json.dumps(progress, ensure_ascii=False)
        requirement.updated_at = datetime.now()
        
        db.session.commit()
        
        logger.info(f"需求启动成功: requirement_id={requirement_id}, 创建了 {len(tasks_created)} 个任务")
        
        return jsonify({
            'code': 200,
            'message': '需求启动成功',
            'data': {
                'requirement': requirement.to_dict(),
                'tasks_created': tasks_created
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"启动需求失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>/progress', methods=['GET'])
def get_requirement_progress(requirement_id):
    """获取需求进度"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        
        # 获取所有关联任务
        req_tasks = RequirementTask.query.filter_by(
            requirement_id=requirement_id
        ).order_by(RequirementTask.task_order).all()
        
        # 构建进度信息
        progress_tasks = []
        total_tasks = len(req_tasks)
        completed_tasks = 0
        current_task_order = None
        
        for req_task in req_tasks:
            # 获取任务详情
            task_info = {
                'id': req_task.id,
                'task_type': req_task.task_type,
                'task_id': req_task.task_id,
                'order': req_task.task_order,
                'status': req_task.status,
                'started_at': req_task.started_at.strftime('%Y-%m-%d %H:%M:%S') if req_task.started_at else None,
                'finished_at': req_task.finished_at.strftime('%Y-%m-%d %H:%M:%S') if req_task.finished_at else None
            }
            
            # 获取任务详细信息
            if req_task.task_type == 'crawler':
                task = CrawlerTask.query.get(req_task.task_id)
                if task:
                    task_info['name'] = task.name
                    task_info['detail'] = task.to_dict()
            elif req_task.task_type == 'cleaning':
                task = DataCleaningTask.query.get(req_task.task_id)
                if task:
                    task_info['name'] = task.name
                    task_info['detail'] = task.to_dict()
            elif req_task.task_type == 'tagging':
                task = TaggingTask.query.get(req_task.task_id)
                if task:
                    task_info['name'] = task.name
                    task_info['detail'] = task.to_dict()
            elif req_task.task_type == 'sample_set':
                task = SampleSet.query.get(req_task.task_id)
                if task:
                    task_info['name'] = task.name
                    task_info['detail'] = task.to_dict()
            
            progress_tasks.append(task_info)
            
            if req_task.status == 'completed':
                completed_tasks += 1
            elif req_task.status == 'running' and current_task_order is None:
                current_task_order = req_task.task_order
            elif current_task_order is None and req_task.status == 'pending':
                current_task_order = req_task.task_order
        
        # 检查是否可以执行下一个任务
        can_execute_next = False
        if current_task_order:
            # 检查前置任务是否都已完成
            prev_tasks = [t for t in req_tasks if t.task_order < current_task_order]
            if all(t.status == 'completed' for t in prev_tasks):
                can_execute_next = True
        
        # 如果所有任务都已完成，更新需求状态为完成
        if completed_tasks == total_tasks and total_tasks > 0:
            if requirement.status != 'completed':
                requirement.status = 'completed'
                requirement.updated_at = datetime.now()
                db.session.commit()
                logger.info(f"所有任务已完成，更新需求状态为完成: requirement_id={requirement_id}")
        
        progress = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'current_task_order': current_task_order,
            'can_execute_next': can_execute_next,
            'tasks': progress_tasks
        }
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': progress
        })
        
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"获取需求进度失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>/execute-next', methods=['POST'])
def execute_next_task(requirement_id):
    """执行需求的下一个任务"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        
        if requirement.status != 'active':
            return jsonify({
                'code': 400,
                'message': f'需求状态为 {requirement.status}，无法执行任务'
            }), 400
        
        # 获取所有关联任务，按顺序排序
        req_tasks = RequirementTask.query.filter_by(
            requirement_id=requirement_id
        ).order_by(RequirementTask.task_order).all()
        
        if not req_tasks:
            return jsonify({
                'code': 400,
                'message': '需求没有关联任务'
            }), 400
        
        # 找到第一个待执行的任务
        next_task = None
        for req_task in req_tasks:
            if req_task.status == 'pending':
                # 检查前置任务是否都已完成
                prev_tasks = [t for t in req_tasks if t.task_order < req_task.task_order]
                if all(t.status == 'completed' for t in prev_tasks):
                    next_task = req_task
                    break
        
        if not next_task:
            # 检查是否所有任务都已完成
            if all(t.status == 'completed' for t in req_tasks):
                if requirement.status != 'completed':
                    requirement.status = 'completed'
                    requirement.updated_at = datetime.now()
                    db.session.commit()
                    logger.info(f"所有任务已完成，更新需求状态为完成: requirement_id={requirement_id}")
                else:
                    # 即使状态已经是completed，也确保更新updated_at
                    requirement.updated_at = datetime.now()
                    db.session.commit()
                return jsonify({
                    'code': 200,
                    'message': '所有任务已完成',
                    'data': {'all_completed': True}
                })
            else:
                return jsonify({
                    'code': 400,
                    'message': '前置任务未完成，无法执行下一个任务'
                }), 400
        
        # 更新任务状态为运行中
        next_task.status = 'running'
        next_task.started_at = datetime.now()
        db.session.commit()
        
        # 根据任务类型执行任务（通过服务层调用，避免循环导入）
        if next_task.task_type == 'crawler':
            # 调用抓取任务执行API（通过HTTP请求模拟）
            import requests
            try:
                response = requests.post(
                    f'http://localhost:8000/api/crawler/tasks/{next_task.task_id}/crawl',
                    timeout=5
                )
            except:
                # 如果请求失败，直接标记为运行中（任务会在后台执行）
                pass
        elif next_task.task_type == 'cleaning':
            # 调用清洗任务执行API
            import requests
            try:
                response = requests.post(
                    f'http://localhost:8000/api/data-cleaning/tasks/{next_task.task_id}/execute',
                    timeout=5
                )
            except:
                pass
        elif next_task.task_type == 'tagging':
            # 调用打标任务执行API
            import requests
            try:
                response = requests.post(
                    f'http://localhost:8000/api/tagging/tasks/{next_task.task_id}/execute',
                    timeout=5
                )
            except:
                pass
        elif next_task.task_type == 'sample_set':
            # 样本集需要计算，调用样本集计算服务
            from app.services.sample_set_service import SampleSetService
            service = SampleSetService()
            result = service.calculate_sample_set_data(next_task.task_id)
            if result['success']:
                next_task.status = 'completed'
                next_task.finished_at = datetime.now()
                db.session.commit()
        
        # 注意：任务执行是异步的，这里只是启动任务
        # 任务完成后需要通过回调或轮询更新RequirementTask的状态
        
        return jsonify({
            'code': 200,
            'message': f'任务已启动: {next_task.task_type}',
            'data': {
                'task_type': next_task.task_type,
                'task_id': next_task.task_id,
                'task_order': next_task.task_order
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"执行下一个任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>/tasks/<int:task_id>/retry', methods=['POST'])
def retry_requirement_task(requirement_id, task_id):
    """重试需求任务"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        req_task = RequirementTask.query.filter_by(
            requirement_id=requirement_id,
            id=task_id
        ).first_or_404()
        
        # 检查任务状态
        if req_task.status not in ['failed', 'completed']:
            return jsonify({
                'code': 400,
                'message': f'任务状态为 {req_task.status}，无法重试'
            }), 400
        
        # 重置任务状态
        req_task.status = 'pending'
        req_task.started_at = None
        req_task.finished_at = None
        
        # 根据任务类型重置原任务状态
        if req_task.task_type == 'crawler':
            task = CrawlerTask.query.get(req_task.task_id)
            if task:
                task.status = 'pending'
                task.started_at = None
                task.finished_at = None
        elif req_task.task_type == 'cleaning':
            task = DataCleaningTask.query.get(req_task.task_id)
            if task:
                task.status = 'pending'
                task.started_at = None
                task.finished_at = None
        elif req_task.task_type == 'tagging':
            task = TaggingTask.query.get(req_task.task_id)
            if task:
                task.status = 'pending'
                task.started_at = None
                task.finished_at = None
        
        db.session.commit()
        
        logger.info(f"需求任务重置成功: requirement_id={requirement_id}, task_id={task_id}")
        
        return jsonify({
            'code': 200,
            'message': '任务已重置，可以重新执行',
            'data': req_task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"重试需求任务失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:requirement_id>/tasks/<int:task_id>/update-status', methods=['PUT'])
def update_requirement_task_status(requirement_id, task_id):
    """手动更新需求任务状态"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        req_task = RequirementTask.query.filter_by(
            requirement_id=requirement_id,
            id=task_id
        ).first_or_404()
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'running', 'completed', 'failed']:
            return jsonify({
                'code': 400,
                'message': '无效的状态值'
            }), 400
        
        req_task.status = new_status
        if new_status == 'running' and not req_task.started_at:
            req_task.started_at = datetime.now()
        elif new_status in ['completed', 'failed']:
            req_task.finished_at = datetime.now()
        
        db.session.commit()
        
        # 更新需求进度
        update_requirement_progress(requirement_id)
        
        return jsonify({
            'code': 200,
            'message': '状态更新成功',
            'data': req_task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"更新需求任务状态失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

def update_requirement_progress(requirement_id):
    """更新需求进度（内部函数）"""
    try:
        requirement = Requirement.query.get(requirement_id)
        if not requirement:
            return
        
        req_tasks = RequirementTask.query.filter_by(
            requirement_id=requirement_id
        ).order_by(RequirementTask.task_order).all()
        
        completed_count = sum(1 for t in req_tasks if t.status == 'completed')
        total_count = len(req_tasks)
        
        # 找到当前任务
        current_task_order = None
        for t in req_tasks:
            if t.status == 'running':
                current_task_order = t.task_order
                break
            elif t.status == 'pending' and current_task_order is None:
                current_task_order = t.task_order
        
        # 如果所有任务完成，更新需求状态
        if completed_count == total_count and total_count > 0:
            if requirement.status != 'completed':
                requirement.status = 'completed'
                requirement.updated_at = datetime.now()
                logger.info(f"需求所有任务已完成，更新需求状态为完成: requirement_id={requirement_id}")
        
        requirement.progress_json = json.dumps({
            'total_tasks': total_count,
            'completed_tasks': completed_count,
            'current_task_order': current_task_order,
            'tasks': []
        }, ensure_ascii=False)
        if requirement.status != 'completed':
            requirement.updated_at = datetime.now()
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新需求进度失败: {str(e)}", exc_info=True)

def check_and_update_requirement_task_status(task_type, task_id):
    """检查并更新需求任务状态（由任务完成时调用）"""
    try:
        # 查找关联的需求任务
        req_task = RequirementTask.query.filter_by(
            task_type=task_type,
            task_id=task_id
        ).first()
        
        if not req_task:
            logger.debug(f"未找到关联的需求任务: task_type={task_type}, task_id={task_id}")
            return
        
        # 根据任务类型获取任务状态（刷新数据库会话以确保获取最新状态）
        task_status = None
        if task_type == 'crawler':
            task = CrawlerTask.query.get(task_id)
            if task:
                db.session.refresh(task)  # 刷新对象以获取最新状态
                task_status = task.status
        elif task_type == 'cleaning':
            task = DataCleaningTask.query.get(task_id)
            if task:
                db.session.refresh(task)  # 刷新对象以获取最新状态
                task_status = task.status
        elif task_type == 'tagging':
            task = TaggingTask.query.get(task_id)
            if task:
                db.session.refresh(task)  # 刷新对象以获取最新状态
                task_status = task.status
        elif task_type == 'sample_set':
            # 样本集没有status字段，需要检查是否已计算完成（通过image_count判断）
            task = SampleSet.query.get(task_id)
            if task:
                db.session.refresh(task)
                # 样本集计算完成的标准：有图片数量且大于0
                if task.image_count and task.image_count > 0:
                    task_status = 'completed'
                else:
                    task_status = 'pending'
        
        if task_status:
            logger.info(f"更新需求任务状态: requirement_id={req_task.requirement_id}, task_type={task_type}, task_id={task_id}, task_status={task_status}")
            # 更新需求任务状态
            if task_status == 'completed':
                req_task.status = 'completed'
                req_task.finished_at = datetime.now()
            elif task_status == 'failed':
                req_task.status = 'failed'
                req_task.finished_at = datetime.now()
            elif task_status == 'running':
                req_task.status = 'running'
                if not req_task.started_at:
                    req_task.started_at = datetime.now()
            
            db.session.commit()
            
            # 更新需求进度（这会检查所有任务是否完成，并更新需求状态）
            update_requirement_progress(req_task.requirement_id)
            logger.info(f"需求任务状态更新成功: requirement_id={req_task.requirement_id}, task_type={task_type}, task_id={task_id}, new_status={req_task.status}")
            
            # 再次检查需求状态，确保已更新
            requirement = Requirement.query.get(req_task.requirement_id)
            if requirement:
                db.session.refresh(requirement)
                logger.info(f"需求当前状态: requirement_id={req_task.requirement_id}, status={requirement.status}")
        else:
            logger.warning(f"无法获取任务状态: task_type={task_type}, task_id={task_id}")
                
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新需求任务状态失败: {str(e)}", exc_info=True)

def check_prerequisite_tasks(task_type, task_id):
    """
    检查前置任务是否完成（用于有需求关联的任务）
    
    Args:
        task_type: 任务类型 ('crawler', 'cleaning', 'tagging', 'sample_set')
        task_id: 任务ID
        
    Returns:
        tuple: (is_ok, error_message)
        - is_ok: True表示前置任务已完成，可以执行；False表示前置任务未完成
        - error_message: 错误提示信息
    """
    try:
        # 查找关联的需求任务
        req_task = RequirementTask.query.filter_by(
            task_type=task_type,
            task_id=task_id
        ).first()
        
        if not req_task:
            # 没有需求关联，允许执行
            return True, None
        
        # 获取需求的所有任务，按顺序检查
        requirement_id = req_task.requirement_id
        req_tasks = RequirementTask.query.filter_by(
            requirement_id=requirement_id
        ).order_by(RequirementTask.task_order).all()
        
        # 找到当前任务的位置
        current_order = req_task.task_order
        
        # 检查所有前置任务（order < current_order）是否都已完成
        for prev_task in req_tasks:
            if prev_task.task_order < current_order:
                if prev_task.status != 'completed':
                    # 前置任务未完成
                    task_type_names = {
                        'crawler': '抓取任务',
                        'cleaning': '清洗任务',
                        'tagging': '打标任务',
                        'sample_set': '样本集'
                    }
                    prev_type_name = task_type_names.get(prev_task.task_type, prev_task.task_type)
                    return False, f"前置任务（{prev_type_name}）尚未完成，请等待前置任务完成后再执行"
        
        return True, None
        
    except Exception as e:
        logger.error(f"检查前置任务失败: {str(e)}", exc_info=True)
        # 出错时允许执行（避免阻塞）
        return True, None

