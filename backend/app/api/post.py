from flask import Blueprint, request, jsonify, send_file, current_app
from app.database import db
from app.models.post import Post
from app.models.post_media import PostMedia
from app.models.post_comment import PostComment
from app.utils.config_manager import get_local_image_dir
from sqlalchemy import case, cast, Integer
import traceback
import os

bp = Blueprint('post', __name__)

@bp.route('', methods=['GET'])
def get_post_list():
    """获取帖子列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        author_name = request.args.get('author_name', type=str)
        search_keyword = request.args.get('search_keyword', type=str)
        sort_by = request.args.get('sort_by', 'crawl_time', type=str)  # 排序字段：crawl_time, like_count
        sort_order = request.args.get('sort_order', 'desc', type=str)  # 排序方向：asc, desc
        
        query = Post.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    Post.title.like(f'%{keyword}%'),
                    Post.content.like(f'%{keyword}%')
                )
            )
        
        if author_name:
            query = query.filter(Post.author_name.like(f'%{author_name}%'))
        
        if search_keyword:
            query = query.filter(Post.search_keyword.like(f'%{search_keyword}%'))
        
        # 排序处理
        if sort_by == 'like_count':
            # 将字符串类型的like_count转换为数字进行排序
            # 处理like_count可能包含"w"（万）、"k"（千）等字符的情况
            # 使用CASE表达式处理不同的格式
            # 提取数字部分并转换单位
            # 如果包含"w"，乘以10000；如果包含"k"，乘以1000；否则直接转换
            # 先移除所有非数字字符（除了小数点），然后根据单位转换
            # MySQL不支持NULLS LAST，使用ISNULL()函数将NULL值放在最后
            like_count_numeric = case(
                (Post.like_count.like('%w%'), 
                 cast(
                     db.func.replace(
                         db.func.replace(
                             db.func.replace(Post.like_count, 'w', ''), 
                             'k', ''
                         ), 
                         '.', ''
                     ), 
                     Integer
                 ) * 10000),
                (Post.like_count.like('%k%'), 
                 cast(
                     db.func.replace(
                         db.func.replace(Post.like_count, 'k', ''), 
                         '.', ''
                     ), 
                     Integer
                 ) * 1000),
                else_=cast(
                    db.func.replace(
                        db.func.replace(
                            db.func.replace(
                                db.func.replace(Post.like_count, '.', ''), 
                                'w', ''
                            ), 
                            'k', ''
                        ), 
                        ' ', ''
                    ), 
                    Integer
                )
            )
            # MySQL兼容的NULL处理：使用ISNULL()将NULL值放在最后
            if sort_order == 'asc':
                # 升序：NULL值放在最后，所以先按ISNULL排序，再按值排序
                query = query.order_by(
                    db.func.isnull(like_count_numeric).asc(),
                    like_count_numeric.asc()
                )
            else:
                # 降序：NULL值放在最后，所以先按ISNULL排序，再按值排序
                query = query.order_by(
                    db.func.isnull(like_count_numeric).asc(),
                    like_count_numeric.desc()
                )
        elif sort_by == 'crawl_time':
            if sort_order == 'asc':
                query = query.order_by(Post.crawl_time.asc())
            else:
                query = query.order_by(Post.crawl_time.desc())
        else:
            # 默认按抓取时间降序
            query = query.order_by(Post.crawl_time.desc())
        
        total = query.count()
        posts = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 获取每个帖子的媒体（图片）
        post_list = []
        for post in posts:
            post_dict = post.to_dict()
            # 获取帖子的第一张图片作为封面
            first_media = PostMedia.query.filter_by(
                post_id=post.post_id,
                media_type='image'
            ).order_by(PostMedia.sort_order).first()
            
            if first_media:
                post_dict['cover_image'] = first_media.media_local_path or first_media.media_url
            else:
                post_dict['cover_image'] = None
            
            post_list.append(post_dict)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': post_list,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    """获取帖子详情（通过数据库ID）"""
    try:
        post = Post.query.get_or_404(post_id)
        post_dict = post.to_dict()
        
        # 获取帖子的所有媒体
        media_list = PostMedia.query.filter_by(
            post_id=post.post_id
        ).order_by(PostMedia.sort_order).all()
        
        post_dict['media'] = [media.to_dict() for media in media_list]
        
        # 获取帖子的所有评论（按时间倒序）
        comments = PostComment.query.filter_by(
            post_id=post.post_id
        ).order_by(PostComment.comment_time.desc()).all()
        
        post_dict['comments'] = [comment.to_dict() for comment in comments]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': post_dict
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/<string:post_id>/media', methods=['GET'])
def get_post_media(post_id):
    """获取帖子的媒体列表"""
    try:
        media_list = PostMedia.query.filter_by(
            post_id=post_id
        ).order_by(PostMedia.sort_order).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [media.to_dict() for media in media_list]
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/media/<int:post_id>', methods=['GET'])
def get_post_cover_image(post_id):
    """获取帖子封面图片URL（返回排序靠前的图片）"""
    try:
        # 获取帖子
        post = Post.query.get_or_404(post_id)
        
        # 获取该帖子排序靠前的第一张图片
        first_media = PostMedia.query.filter_by(
            post_id=post.post_id,
            media_type='image'
        ).order_by(PostMedia.sort_order).first()
        
        if not first_media:
            return jsonify({
                'code': 404,
                'message': '该帖子没有图片'
            }), 404
        
        # 优先使用本地路径
        if first_media.media_local_path:
            file_path = first_media.media_local_path
            
            # 规范化路径（统一使用正斜杠）
            relative_path = file_path.replace('\\', '/')
            
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
                media_url = f'/api/posts/media/{post_id}/content'
                current_app.logger.info(f"返回帖子封面URL: {media_url}, 文件路径: {file_path}")
                return jsonify({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'url': media_url
                    }
                })
        
        # 如果没有本地路径或文件不存在，使用原始URL
        if first_media.media_url:
            current_app.logger.info(f"返回帖子封面原始URL: {first_media.media_url}")
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'url': first_media.media_url
                }
            })
        
        return jsonify({
            'code': 404,
            'message': '该帖子没有可用的图片'
        }), 404
        
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取帖子封面图片失败，ID: {post_id}, 错误: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/media/<int:post_id>/content', methods=['GET'])
def get_post_cover_image_content(post_id):
    """获取帖子封面图片文件内容（实际文件流）"""
    try:
        # 获取帖子
        post = Post.query.get_or_404(post_id)
        
        # 获取该帖子排序靠前的第一张图片
        first_media = PostMedia.query.filter_by(
            post_id=post.post_id,
            media_type='image'
        ).order_by(PostMedia.sort_order).first()
        
        if not first_media or not first_media.media_local_path:
            return jsonify({'code': 404, 'message': '该帖子没有本地图片文件'}), 404
        
        file_path = first_media.media_local_path
        
        # 规范化路径（统一使用正斜杠）
        relative_path = file_path.replace('\\', '/')
        
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
            current_app.logger.info(f"返回帖子封面图片文件: {file_path}")
            # 使用 mimetype 参数确保正确识别图片类型
            mimetype = None
            if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                mimetype = 'image/jpeg'
            elif file_path.lower().endswith('.png'):
                mimetype = 'image/png'
            elif file_path.lower().endswith('.gif'):
                mimetype = 'image/gif'
            elif file_path.lower().endswith('.webp'):
                mimetype = 'image/webp'
            return send_file(file_path, mimetype=mimetype)
        else:
            current_app.logger.warning(f"图片文件不存在: {file_path}, 原始media_local_path: {first_media.media_local_path}")
            return jsonify({'code': 404, 'message': '图片文件不存在'}), 404
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取帖子封面图片内容失败，ID: {post_id}, 错误: {error_detail}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/media/item/<int:media_id>/content', methods=['GET'])
def get_post_media_content(media_id):
    """获取帖子媒体文件内容（通过media_id）"""
    try:
        # 获取媒体记录
        media = PostMedia.query.get_or_404(media_id)
        
        if not media.media_local_path:
            return jsonify({'code': 404, 'message': '该媒体没有本地文件'}), 404
        
        file_path = media.media_local_path
        
        # 规范化路径（统一使用正斜杠）
        relative_path = file_path.replace('\\', '/')
        
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
            current_app.logger.info(f"返回帖子媒体文件: {file_path}")
            # 使用 mimetype 参数确保正确识别图片类型
            mimetype = None
            if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                mimetype = 'image/jpeg'
            elif file_path.lower().endswith('.png'):
                mimetype = 'image/png'
            elif file_path.lower().endswith('.gif'):
                mimetype = 'image/gif'
            elif file_path.lower().endswith('.webp'):
                mimetype = 'image/webp'
            return send_file(file_path, mimetype=mimetype)
        else:
            current_app.logger.warning(f"媒体文件不存在: {file_path}, 原始media_local_path: {media.media_local_path}")
            return jsonify({'code': 404, 'message': '文件不存在'}), 404
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取帖子媒体内容失败，ID: {media_id}, 错误: {error_detail}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """获取帖子评论列表"""
    try:
        # 获取帖子
        post = Post.query.get_or_404(post_id)
        
        # 获取评论列表
        comments = PostComment.query.filter_by(
            post_id=post.post_id
        ).order_by(PostComment.comment_time.desc()).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [comment.to_dict() for comment in comments]
        })
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500


