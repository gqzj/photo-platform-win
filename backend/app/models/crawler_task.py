from app.database import db
from datetime import datetime

class CrawlerTask(db.Model):
    """爬虫任务模型"""
    __tablename__ = 'crawler_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, default='任务', comment='任务名称')
    platform = db.Column(db.String(100), nullable=False, comment='平台名称')
    task_type = db.Column(db.String(50), nullable=False, default='generic', comment='任务类型')
    target_url = db.Column(db.String(2000), nullable=True, comment='目标URL')
    cookie_id = db.Column(db.Integer, nullable=True, comment='关联的Cookie ID')
    status = db.Column(db.String(50), nullable=False, comment='状态：pending, running, paused, completed, failed')
    config_json = db.Column(db.Text, comment='配置JSON')
    keywords_json = db.Column(db.Text, comment='关键词JSON')
    tags_json = db.Column(db.Text, comment='标签JSON')
    progress_json = db.Column(db.Text, comment='进度JSON')
    note = db.Column(db.Text, comment='备注')
    last_error = db.Column(db.Text, comment='最后错误信息')
    current_keyword = db.Column(db.String(200), comment='当前关键词')
    processed_posts = db.Column(db.Integer, nullable=False, default=0, comment='已处理帖子数')
    processed_comments = db.Column(db.Integer, nullable=False, default=0, comment='已处理评论数')
    downloaded_media = db.Column(db.Integer, nullable=False, default=0, comment='已下载媒体数')
    started_at = db.Column(db.DateTime, comment='开始时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        import json
        result = {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'task_type': self.task_type,
            'target_url': self.target_url or '',
            'cookie_id': self.cookie_id,
            'status': self.status,
            'config_json': self.config_json,
            'keywords_json': self.keywords_json,
            'tags_json': self.tags_json,
            'progress_json': self.progress_json,
            'note': self.note or '',
            'last_error': self.last_error or '',
            'current_keyword': self.current_keyword or '',
            'processed_posts': self.processed_posts,
            'processed_comments': self.processed_comments,
            'downloaded_media': self.downloaded_media,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        return result

