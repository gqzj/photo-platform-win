from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.crawler_task import CrawlerTask
from app.models.crawler_cookie import CrawlerCookie
from app.models.keyword_statistics import KeywordStatistics
from datetime import datetime
import logging
import json
import traceback
import threading

bp = Blueprint('crawler_task', __name__)
logger = logging.getLogger(__name__)

def get_crawler_service():
    """延迟导入爬虫服务，避免循环导入"""
    from app.services.xiaohongshu_crawler_service import XiaohongshuCrawlerService
    return XiaohongshuCrawlerService()

@bp.route('', methods=['GET'])
def get_task_list():
    """获取任务列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        platform = request.args.get('platform', type=str)
        status = request.args.get('status', type=str)
        task_type = request.args.get('task_type', type=str)
        
        query = CrawlerTask.query
        
        if platform:
            query = query.filter(CrawlerTask.platform == platform)
        if status:
            query = query.filter(CrawlerTask.status == status)
        if task_type:
            query = query.filter(CrawlerTask.task_type == task_type)
        
        total = query.count()
        tasks = query.order_by(CrawlerTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
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
        error_detail = traceback.format_exc()
        logger.error(f"Error in get_task_list: {str(e)}")
        logger.error(error_detail)
        current_app.logger.error(f"Error in get_task_list: {str(e)}")
        current_app.logger.error(error_detail)
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>/refresh', methods=['POST'])
def refresh_task(task_id):
    """刷新任务状态和统计数据"""
    try:
        task = CrawlerTask.query.get_or_404(task_id)
        
        # 刷新任务状态（从数据库重新加载）
        db.session.refresh(task)
        
        # 如果任务状态为完成，重新统计数据
        if task.status == 'completed':
            from app.models.post import Post
            from app.models.post_media import PostMedia
            from sqlalchemy import func
            
            # 获取任务的关键字列表
            keywords = []
            if task.keywords_json:
                try:
                    keywords = json.loads(task.keywords_json)
                    if not isinstance(keywords, list):
                        keywords = []
                except:
                    keywords = []
            
            # 统计帖子数：根据search_keyword匹配
            post_count = 0
            media_count = 0
            comment_count = 0
            
            if keywords:
                # 统计每个关键字对应的帖子数
                for keyword in keywords:
                    if keyword:
                        # 统计帖子数
                        posts = Post.query.filter(Post.search_keyword == keyword).all()
                        post_count += len(posts)
                        
                        # 统计媒体数：统计这些帖子对应的媒体
                        post_ids = [post.post_id for post in posts]
                        if post_ids:
                            media_count += PostMedia.query.filter(PostMedia.post_id.in_(post_ids)).count()
                        
                        # 统计评论数：累加帖子的comment_count字段
                        for post in posts:
                            try:
                                comment_count += int(post.comment_count) if post.comment_count else 0
                            except (ValueError, TypeError):
                                pass
            
            # 更新任务统计数据
            task.processed_posts = post_count
            task.processed_comments = comment_count
            task.downloaded_media = media_count
            
            # 更新进度JSON
            progress = {
                'posts': post_count,
                'comments': comment_count,
                'media': media_count,
                'images': media_count  # 媒体数作为图片数
            }
            if task.progress_json:
                try:
                    old_progress = json.loads(task.progress_json)
                    if isinstance(old_progress, dict):
                        progress.update(old_progress)
                except:
                    pass
            task.progress_json = json.dumps(progress, ensure_ascii=False)
            
            task.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"任务 {task_id} 统计数据已刷新: 帖子={post_count}, 评论={comment_count}, 媒体={media_count}")
        
        return jsonify({
            'code': 200,
            'message': '刷新成功',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        logger.error(f"刷新任务失败，任务ID: {task_id}: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:task_id>', methods=['GET'])
def get_task_detail(task_id):
    """获取任务详情"""
    try:
        task = CrawlerTask.query.get_or_404(task_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': task.to_dict()
        })
    except Exception as e:
        logger.error(f"Error in get_task_detail: {str(e)}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('', methods=['POST'])
def create_task():
    """创建任务"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name') or not data.get('platform') or not data.get('task_type'):
            return jsonify({'code': 400, 'message': 'name、platform和task_type为必填项'}), 400
        
        # 根据任务类型验证相应字段
        if data.get('task_type') == 'url':
            if not data.get('target_url'):
                return jsonify({'code': 400, 'message': '目标URL类型任务需要填写target_url'}), 400
        elif data.get('task_type') == 'keyword':
            if not data.get('keywords_json'):
                return jsonify({'code': 400, 'message': '关键字爬取类型任务需要填写关键字'}), 400
        
        # 处理时间字段
        started_at = None
        finished_at = None
        if data.get('started_at'):
            try:
                started_at = datetime.strptime(data['started_at'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        if data.get('finished_at'):
            try:
                finished_at = datetime.strptime(data['finished_at'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        task = CrawlerTask(
            name=data['name'],
            platform=data['platform'],
            task_type=data.get('task_type', 'keyword'),
            target_url=data.get('target_url', ''),
            cookie_id=data.get('cookie_id'),
            status=data.get('status', 'pending'),
            config_json=data.get('config_json'),
            keywords_json=data.get('keywords_json'),
            tags_json=data.get('tags_json'),
            progress_json=data.get('progress_json'),
            note=data.get('note'),
            last_error=data.get('last_error'),
            current_keyword=data.get('current_keyword'),
            processed_posts=data.get('processed_posts', 0),
            processed_comments=data.get('processed_comments', 0),
            downloaded_media=data.get('downloaded_media', 0),
            started_at=started_at,
            finished_at=finished_at,
            created_at=datetime.now(),
            updated_at=datetime.now()
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
        logger.error(f"Error in create_task: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    try:
        task = CrawlerTask.query.get_or_404(task_id)
        data = request.get_json()
        
        if 'name' in data:
            task.name = data['name']
        if 'platform' in data:
            task.platform = data['platform']
        if 'task_type' in data:
            task.task_type = data['task_type']
        if 'target_url' in data:
            task.target_url = data['target_url']
        if 'cookie_id' in data:
            task.cookie_id = data['cookie_id'] if data['cookie_id'] else None
        if 'status' in data:
            task.status = data['status']
        if 'config_json' in data:
            task.config_json = data['config_json']
        if 'keywords_json' in data:
            task.keywords_json = data['keywords_json']
        if 'tags_json' in data:
            task.tags_json = data['tags_json']
        if 'progress_json' in data:
            task.progress_json = data['progress_json']
        if 'note' in data:
            task.note = data['note']
        if 'last_error' in data:
            task.last_error = data['last_error']
        if 'current_keyword' in data:
            task.current_keyword = data['current_keyword']
        if 'processed_posts' in data:
            task.processed_posts = data['processed_posts']
        if 'processed_comments' in data:
            task.processed_comments = data['processed_comments']
        if 'downloaded_media' in data:
            task.downloaded_media = data['downloaded_media']
        if 'started_at' in data:
            if data['started_at']:
                try:
                    task.started_at = datetime.strptime(data['started_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    pass
            else:
                task.started_at = None
        if 'finished_at' in data:
            if data['finished_at']:
                try:
                    task.finished_at = datetime.strptime(data['finished_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    pass
            else:
                task.finished_at = None
        
        task.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in update_task: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        task = CrawlerTask.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in delete_task: {str(e)}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/batch', methods=['DELETE'])
def batch_delete_tasks():
    """批量删除任务"""
    try:
        data = request.get_json()
        task_ids = data.get('ids', [])
        
        if not task_ids:
            return jsonify({'code': 400, 'message': '请选择要删除的任务'}), 400
        
        CrawlerTask.query.filter(CrawlerTask.id.in_(task_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '批量删除成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in batch_delete_tasks: {str(e)}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:task_id>/crawl', methods=['POST'])
def crawl_task(task_id):
    """执行抓取任务"""
    current_app.logger.info(f"开始执行抓取任务，ID: {task_id}")
    try:
        task = CrawlerTask.query.get_or_404(task_id)
        
        # 检查任务是否已经在运行
        if task.status == 'running':
            # 检查是否运行超时（超过30分钟认为是异常）
            if task.started_at:
                from datetime import timedelta
                if datetime.now() - task.started_at > timedelta(minutes=30):
                    current_app.logger.warning(f"任务 {task_id} 运行超时，重置状态")
                    task.status = 'pending'
                    task.started_at = None
                    db.session.commit()
                else:
                    return jsonify({'code': 400, 'message': '任务正在运行中，请稍候'}), 400
        
        # 验证任务类型
        if task.task_type != 'keyword':
            return jsonify({'code': 400, 'message': '当前只支持关键字爬取类型的任务'}), 400
        
        # 获取关键字
        keywords = []
        if task.keywords_json:
            try:
                keywords = json.loads(task.keywords_json)
            except:
                return jsonify({'code': 400, 'message': '关键字格式错误'}), 400
        
        if not keywords:
            return jsonify({'code': 400, 'message': '请先设置关键字'}), 400
        
        # 检查是否有其他任务正在运行（除了当前任务）
        running_task = CrawlerTask.query.filter(
            CrawlerTask.status == 'running',
            CrawlerTask.id != task_id
        ).first()
        
        if running_task:
            # 检查运行中的任务是否超时（超过30分钟认为是异常）
            if running_task.started_at:
                from datetime import timedelta
                if datetime.now() - running_task.started_at > timedelta(minutes=30):
                    current_app.logger.warning(f"任务 {running_task.id} 运行超时，重置状态")
                    running_task.status = 'pending'
                    running_task.started_at = None
                    db.session.commit()
                else:
                    return jsonify({
                        'code': 400, 
                        'message': f'有其他任务（ID: {running_task.id}, 名称: {running_task.name}）正在运行中，请等待完成后再执行'
                    }), 400
        
        # 获取Cookie（优先使用任务指定的cookie_id，否则使用active状态的）
        cookie_json_str = None
        cookie = None
        
        if task.cookie_id:
            # 使用任务指定的cookie
            cookie = CrawlerCookie.query.filter_by(
                id=task.cookie_id,
                platform=task.platform
            ).first()
            if cookie and cookie.cookie_json:
                cookie_json_str = cookie.cookie_json
                current_app.logger.info(f"使用任务指定的Cookie，ID: {task.cookie_id}, 平台: {task.platform}, 账号: {cookie.platform_account}")
            else:
                current_app.logger.warning(f"任务指定的Cookie不存在或无效，ID: {task.cookie_id}, 平台: {task.platform}")
        
        if not cookie_json_str:
            # 如果没有指定cookie或指定的cookie无效，使用active状态的cookie
            cookie = CrawlerCookie.query.filter_by(
                platform=task.platform,
                status='active'
            ).first()
            
            if cookie and cookie.cookie_json:
                cookie_json_str = cookie.cookie_json
                current_app.logger.info(f"使用默认Cookie，平台: {task.platform}, 账号: {cookie.platform_account}")
            else:
                current_app.logger.warning(f"未找到有效的Cookie，平台: {task.platform}")
        
        # 更新任务状态为运行中
        task.status = 'running'
        task.started_at = datetime.now()
        task.last_error = None
        db.session.commit()
        
        # 获取配置中的每个关键字最大抓取帖子数
        max_posts_per_keyword = 200  # 默认每个关键字抓取200个帖子，可以从配置中读取
        if task.config_json:
            try:
                config = json.loads(task.config_json)
                max_posts_per_keyword = config.get('max_posts_per_keyword', 200)
            except:
                pass
        
        current_app.logger.info(f"开始抓取，关键字数量: {len(keywords)}, 每个关键字最大帖子数: {max_posts_per_keyword}, 任务ID: {task_id}")
        current_app.logger.info(f"将跳过已抓取的关键字（在keyword_statistics表中）")
        
        # 在后台线程中执行抓取，避免阻塞HTTP请求和Flask自动重载
        def run_crawl():
            """在后台线程中执行抓取"""
            # 禁用Flask的自动重载，避免Playwright文件变化触发重启
            import os
            original_reloader = os.environ.get('FLASK_RUN_RELOAD')
            os.environ['FLASK_RUN_RELOAD'] = 'false'
            
            try:
                # 需要导入app来创建新的应用上下文
                from app import create_app
                app_instance = create_app()
                # 禁用自动重载
                app_instance.config['DEBUG'] = False
                with app_instance.app_context():
                    try:
                        crawler_service = get_crawler_service()
                        
                        # 累计所有关键字的统计信息
                        total_stats = {
                            'posts': 0,
                            'comments': 0,
                            'media': 0,
                            'images': 0,
                            'errors': [],
                            'keywords': []  # 记录每个关键字的处理结果
                        }
                        
                        # 顺序处理每个关键字
                        processed_count = 0
                        skipped_count = 0
                        for idx, keyword in enumerate(keywords):
                            if not keyword or not keyword.strip():
                                continue
                            
                            keyword = keyword.strip()
                            
                            # 检查关键字是否已经抓取过（在keyword_statistics表中）
                            existing_keyword = KeywordStatistics.query.filter_by(keyword=keyword).first()
                            if existing_keyword:
                                skipped_count += 1
                                current_app.logger.info(f"跳过已抓取的关键字 [{idx + 1}/{len(keywords)}]: {keyword} (已有 {existing_keyword.image_count} 张图片)")
                                total_stats['keywords'].append({
                                    'keyword': keyword,
                                    'success': True,
                                    'skipped': True,
                                    'message': f'已抓取过，跳过（已有 {existing_keyword.image_count} 张图片）'
                                })
                                continue
                            
                            processed_count += 1
                            current_app.logger.info(f"开始处理关键字 [{idx + 1}/{len(keywords)}]: {keyword}")
                            
                            # 更新当前关键字
                            task = CrawlerTask.query.get(task_id)
                            if task:
                                task.current_keyword = f"{keyword} ({idx + 1}/{len(keywords)})"
                                db.session.commit()
                            
                            try:
                                # 执行单个关键字的抓取
                                result = crawler_service.crawl_by_keyword(
                                    keyword=keyword,
                                    cookie_json_str=cookie_json_str,
                                    max_posts=max_posts_per_keyword,
                                    task_id=task_id
                                )
                                
                                # 累计统计信息
                                if result.get('success'):
                                    total_stats['posts'] += result['stats'].get('posts', 0)
                                    total_stats['comments'] += result['stats'].get('comments', 0)
                                    total_stats['media'] += result['stats'].get('media', 0)
                                    total_stats['images'] += result['stats'].get('images', 0)
                                    total_stats['errors'].extend(result['stats'].get('errors', []))
                                    
                                    total_stats['keywords'].append({
                                        'keyword': keyword,
                                        'success': True,
                                        'stats': result['stats']
                                    })
                                    
                                    current_app.logger.info(f"关键字 '{keyword}' 抓取完成，统计: {result['stats']}")
                                else:
                                    error_msg = f"关键字 '{keyword}' 抓取失败: {result.get('message', '未知错误')}"
                                    total_stats['errors'].append(error_msg)
                                    total_stats['keywords'].append({
                                        'keyword': keyword,
                                        'success': False,
                                        'error': result.get('message', '未知错误')
                                    })
                                    current_app.logger.error(error_msg)
                                    
                                    # 更新任务进度（即使失败也更新）
                                    task = CrawlerTask.query.get(task_id)
                                    if task:
                                        task.processed_posts = total_stats['posts']
                                        task.processed_comments = total_stats['comments']
                                        task.downloaded_media = total_stats['media']
                                        progress = {
                                            'posts': total_stats['posts'],
                                            'comments': total_stats['comments'],
                                            'media': total_stats['media'],
                                            'images': total_stats['images'],
                                            'errors': total_stats['errors'],
                                            'keywords': total_stats['keywords']
                                        }
                                        task.progress_json = json.dumps(progress, ensure_ascii=False)
                                        db.session.commit()
                                
                            except Exception as e:
                                error_msg = f"关键字 '{keyword}' 处理异常: {str(e)}"
                                total_stats['errors'].append(error_msg)
                                total_stats['keywords'].append({
                                    'keyword': keyword,
                                    'success': False,
                                    'error': str(e)
                                })
                                current_app.logger.error(error_msg, exc_info=True)
                                
                                # 继续处理下一个关键字，不中断整个任务
                                continue
                        
                        # 所有关键字处理完成，更新任务状态
                        task = CrawlerTask.query.get(task_id)
                        if task:
                            # 判断任务是否成功（至少有一个关键字成功）
                            has_success = any(k.get('success', False) and not k.get('skipped', False) for k in total_stats['keywords'])
                            
                            if has_success:
                                task.status = 'completed'
                                task.finished_at = datetime.now()
                                task.processed_posts = total_stats['posts']
                                task.processed_comments = total_stats['comments']
                                task.downloaded_media = total_stats['media']
                                task.current_keyword = f"已完成 ({len(keywords)}/{len(keywords)})"
                                task.last_error = None
                                
                                # 更新进度JSON
                                progress = {
                                    'posts': total_stats['posts'],
                                    'comments': total_stats['comments'],
                                    'media': total_stats['media'],
                                    'images': total_stats['images'],
                                    'errors': total_stats['errors'],
                                    'keywords': total_stats['keywords']
                                }
                                task.progress_json = json.dumps(progress, ensure_ascii=False)
                                
                                current_app.logger.info(f"抓取任务完成，任务ID: {task_id}, 处理关键字数: {processed_count}, 跳过关键字数: {skipped_count}, 总统计: {total_stats}")
                                
                                # 刷新关键字统计记录
                                try:
                                    from app.models.image import Image
                                    from sqlalchemy import func
                                    
                                    # 清空现有数据
                                    KeywordStatistics.query.delete()
                                    
                                    # 从images表统计关键字
                                    results = db.session.query(
                                        Image.keyword,
                                        func.count(Image.id).label('image_count')
                                    ).filter(
                                        Image.keyword.isnot(None),
                                        Image.keyword != ''
                                    ).group_by(Image.keyword).all()
                                    
                                    # 批量插入
                                    keyword_stats = []
                                    for keyword, count in results:
                                        keyword_stat = KeywordStatistics(
                                            keyword=keyword,
                                            image_count=count
                                        )
                                        keyword_stats.append(keyword_stat)
                                    
                                    if keyword_stats:
                                        db.session.bulk_save_objects(keyword_stats)
                                    
                                    db.session.commit()
                                    current_app.logger.info(f"关键字统计已刷新，共 {len(keyword_stats)} 个关键字")
                                except Exception as refresh_error:
                                    current_app.logger.error(f"刷新关键字统计失败: {str(refresh_error)}", exc_info=True)
                                    db.session.rollback()
                            else:
                                # 所有关键字都失败
                                task.status = 'failed'
                                task.finished_at = datetime.now()
                                task.last_error = '所有关键字抓取都失败'
                                current_app.logger.error(f"抓取任务失败，任务ID: {task_id}: 所有关键字抓取都失败")
                            
                            db.session.commit()
                            
                    except Exception as e:
                        current_app.logger.error(f"后台抓取任务异常，任务ID: {task_id}: {str(e)}", exc_info=True)
                        try:
                            task = CrawlerTask.query.get(task_id)
                            if task:
                                task.status = 'failed'
                                task.last_error = str(e)
                                task.finished_at = datetime.now()
                                db.session.commit()
                        except:
                            pass
            finally:
                # 恢复原始的重载设置
                if original_reloader is not None:
                    os.environ['FLASK_RUN_RELOAD'] = original_reloader
                elif 'FLASK_RUN_RELOAD' in os.environ:
                    del os.environ['FLASK_RUN_RELOAD']
        
        # 启动后台线程
        thread = threading.Thread(target=run_crawl, daemon=True)
        thread.start()
        
        # 立即返回响应
        return jsonify({
            'code': 200,
            'message': '抓取任务已启动，正在后台执行',
            'data': {
                'task': task.to_dict(),
                'stats': {
                    'posts': 0,
                    'comments': 0,
                    'media': 0,
                    'images': 0
                }
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = f"执行抓取任务异常，任务ID: {task_id}: {str(e)}"
        current_app.logger.error(error_detail, exc_info=True)
        
        # 更新任务状态为失败
        try:
            task = CrawlerTask.query.get(task_id)
            if task:
                task.status = 'failed'
                task.last_error = str(e)
                task.finished_at = datetime.now()
                db.session.commit()
        except:
            pass
        
        return jsonify({'code': 500, 'message': f'服务器内部错误: {str(e)}'}), 500

