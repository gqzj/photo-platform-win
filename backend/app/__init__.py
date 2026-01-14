from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.database import db
import logging
import os
from datetime import datetime

def setup_logging(app):
    """配置日志"""
    # 创建logs目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    error_log_file = os.path.join(log_dir, f'error_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    # 配置错误日志文件
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # 获取Flask的日志记录器
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.addHandler(error_handler)
    
    # 获取应用日志记录器
    app_logger = logging.getLogger(__name__)
    app_logger.addHandler(error_handler)
    
    app.logger.info(f'日志文件位置: {log_file}')
    app.logger.info(f'错误日志文件位置: {error_log_file}')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 配置日志
    setup_logging(app)
    
    # 初始化数据库
    db.init_app(app)
    
    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册蓝图
    from app.api import image_capture, image_tagging, image_statistics, crawler_cookie, crawler_task, post, settings, feature, data_cleaning_task, image_recycle, tagging_task, image_cleaning_test, image_tagging_test, sample_set, keyword_statistics, feature_analysis, requirement, feature_group, style, style_match, lut_category, lut_file, sample_image, tools, semantic_search, manual_style, feature_style_definition, feature_query
    
    app.register_blueprint(image_capture.bp, url_prefix='/api/images/capture')
    app.register_blueprint(image_tagging.bp, url_prefix='/api/images')
    app.register_blueprint(image_statistics.bp, url_prefix='/api/statistics')
    app.register_blueprint(crawler_cookie.bp, url_prefix='/api/crawler/cookies')
    app.register_blueprint(crawler_task.bp, url_prefix='/api/crawler/tasks')
    app.register_blueprint(post.bp, url_prefix='/api/posts')
    app.register_blueprint(settings.bp, url_prefix='/api/settings')
    app.register_blueprint(feature.bp, url_prefix='/api/features')
    app.register_blueprint(data_cleaning_task.bp, url_prefix='/api/data-cleaning/tasks')
    app.register_blueprint(tagging_task.bp, url_prefix='/api/tagging/tasks')
    app.register_blueprint(image_recycle.bp, url_prefix='/api/images/recycle')
    app.register_blueprint(image_cleaning_test.bp, url_prefix='/api/image-cleaning-test')
    app.register_blueprint(image_tagging_test.bp, url_prefix='/api/image-tagging-test')
    app.register_blueprint(sample_set.bp, url_prefix='/api/sample-sets')
    app.register_blueprint(keyword_statistics.bp, url_prefix='/api/keyword-statistics')
    app.register_blueprint(feature_analysis.bp, url_prefix='/api/feature-analysis')
    app.register_blueprint(requirement.bp, url_prefix='/api/requirements')
    app.register_blueprint(feature_group.bp, url_prefix='/api/feature-groups')
    app.register_blueprint(style.bp, url_prefix='/api/styles')
    app.register_blueprint(style_match.bp, url_prefix='/api/style-match')
    app.register_blueprint(lut_category.bp, url_prefix='/api/lut-categories')
    app.register_blueprint(lut_file.bp, url_prefix='/api/lut-files')
    app.register_blueprint(sample_image.bp, url_prefix='/api/sample-images')
    app.register_blueprint(tools.bp, url_prefix='/api/tools')
    app.register_blueprint(semantic_search.bp, url_prefix='/api/semantic-search')
    app.register_blueprint(manual_style.bp, url_prefix='/api/manual-styles')
    app.register_blueprint(feature_style_definition.bp, url_prefix='/api/feature-style-definitions')
    app.register_blueprint(feature_query.bp, url_prefix='/api/feature-query')
    
    return app

