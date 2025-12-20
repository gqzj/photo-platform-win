from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.crawler_cookie import CrawlerCookie
from app.services.cookie_fetcher_service import CookieFetcherService
from datetime import datetime
import logging

bp = Blueprint('crawler_cookie', __name__)
cookie_fetcher = CookieFetcherService()
logger = logging.getLogger(__name__)

@bp.route('', methods=['GET'])
def get_cookie_list():
    """获取Cookie列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        platform = request.args.get('platform', type=str)
        status = request.args.get('status', type=str)
        
        query = CrawlerCookie.query
        
        if platform:
            query = query.filter(CrawlerCookie.platform == platform)
        if status:
            query = query.filter(CrawlerCookie.status == status)
        
        total = query.count()
        cookies = query.order_by(CrawlerCookie.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': [cookie.to_dict() for cookie in cookies],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in get_cookie_list: {error_detail}")
        # 如果是表不存在的错误，返回更友好的提示
        error_msg = str(e)
        if 'Table' in error_msg and "doesn't exist" in error_msg:
            error_msg = "数据库表 crawler_cookies 不存在，请先执行 create_table.sql 创建表"
        return jsonify({'code': 500, 'message': error_msg}), 500

@bp.route('/<int:cookie_id>', methods=['GET'])
def get_cookie_detail(cookie_id):
    """获取Cookie详情（包含敏感字段）"""
    try:
        cookie = CrawlerCookie.query.get_or_404(cookie_id)
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': cookie.to_dict(include_sensitive=True)
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('', methods=['POST'])
def create_cookie():
    """创建Cookie"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('platform') or not data.get('acquire_type'):
            return jsonify({'code': 400, 'message': 'platform和acquire_type为必填项'}), 400
        
        cookie = CrawlerCookie(
            platform=data['platform'],
            note=data.get('note'),
            cookie_json=data.get('cookie_json'),
            platform_account=data.get('platform_account'),
            acquire_type=data['acquire_type'],
            login_method=data.get('login_method'),
            password=data.get('password'),
            verification_code=data.get('verification_code'),
            status=data.get('status', 'active'),
            last_error=data.get('last_error'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if data.get('fetched_at'):
            try:
                cookie.fetched_at = datetime.strptime(data['fetched_at'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(cookie)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': cookie.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:cookie_id>', methods=['PUT'])
def update_cookie(cookie_id):
    """更新Cookie"""
    try:
        cookie = CrawlerCookie.query.get_or_404(cookie_id)
        data = request.get_json()
        
        if 'platform' in data:
            cookie.platform = data['platform']
        if 'note' in data:
            cookie.note = data['note']
        if 'cookie_json' in data:
            cookie.cookie_json = data['cookie_json']
        if 'platform_account' in data:
            cookie.platform_account = data['platform_account']
        if 'acquire_type' in data:
            cookie.acquire_type = data['acquire_type']
        if 'login_method' in data:
            cookie.login_method = data['login_method']
        if 'password' in data:
            cookie.password = data['password']
        if 'verification_code' in data:
            cookie.verification_code = data['verification_code']
        if 'status' in data:
            cookie.status = data['status']
        if 'last_error' in data:
            cookie.last_error = data['last_error']
        if 'fetched_at' in data:
            if data['fetched_at']:
                try:
                    cookie.fetched_at = datetime.strptime(data['fetched_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    return jsonify({'code': 400, 'message': '抓取时间格式错误'}), 400
            else:
                cookie.fetched_at = None
        
        cookie.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': cookie.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:cookie_id>', methods=['DELETE'])
def delete_cookie(cookie_id):
    """删除Cookie"""
    try:
        cookie = CrawlerCookie.query.get_or_404(cookie_id)
        db.session.delete(cookie)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/batch', methods=['DELETE'])
def batch_delete_cookies():
    """批量删除Cookie"""
    try:
        data = request.get_json()
        cookie_ids = data.get('ids', [])
        
        if not cookie_ids:
            return jsonify({'code': 400, 'message': '请选择要删除的Cookie'}), 400
        
        CrawlerCookie.query.filter(CrawlerCookie.id.in_(cookie_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '批量删除成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500

@bp.route('/<int:cookie_id>/fetch', methods=['POST'])
def fetch_cookie(cookie_id):
    """获取Cookie（使用Playwright自动登录）"""
    try:
        cookie = CrawlerCookie.query.get_or_404(cookie_id)
        
        # 验证必要字段
        if not cookie.platform_account:
            return jsonify({'code': 400, 'message': '请先设置平台账号'}), 400
        
        if cookie.acquire_type != 'auto':
            return jsonify({'code': 400, 'message': '只有自动获取类型才能使用此功能'}), 400
        
        if not cookie.login_method:
            return jsonify({'code': 400, 'message': '请先设置登录方式'}), 400
        
        # 根据登录方式获取相应参数
        if cookie.login_method == 'password':
            if not cookie.password:
                return jsonify({'code': 400, 'message': '请先设置密码'}), 400
            result = cookie_fetcher.fetch_cookie(
                platform=cookie.platform,
                account=cookie.platform_account,
                login_method='password',
                password=cookie.password
            )
        elif cookie.login_method == 'sms':
            if not cookie.verification_code:
                return jsonify({'code': 400, 'message': '请先设置验证码'}), 400
            result = cookie_fetcher.fetch_cookie(
                platform=cookie.platform,
                account=cookie.platform_account,
                login_method='sms',
                verification_code=cookie.verification_code
            )
        else:
            return jsonify({'code': 400, 'message': '不支持的登录方式'}), 400
        
        if result['success']:
            # 更新cookie_json
            cookie.cookie_json = result['cookie_json']
            cookie.status = 'active'
            cookie.last_error = None
            cookie.updated_at = datetime.now()
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'message': result['message'],
                'data': cookie.to_dict()
            })
        else:
            # 更新错误信息
            cookie.last_error = result['message']
            cookie.status = 'error'
            cookie.updated_at = datetime.now()
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'message': result['message'],
                'data': None
            }), 500
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        
        # 记录错误日志
        logger.error(f"Error in fetch_cookie (cookie_id={cookie_id}): {error_detail}")
        
        db.session.rollback()
        
        # 更新错误信息到数据库
        try:
            cookie = CrawlerCookie.query.get(cookie_id)
            if cookie:
                cookie.last_error = str(e)
                cookie.status = 'error'
                cookie.updated_at = datetime.now()
                db.session.commit()
        except:
            pass
        
        return jsonify({
            'code': 500,
            'message': f'获取Cookie失败: {str(e)}',
            'detail': error_detail
        }), 500

