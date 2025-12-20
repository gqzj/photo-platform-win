# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class TaggingTask(db.Model):
    """数据打标任务模型"""
    __tablename__ = 'tagging_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, comment='任务名称')
    description = db.Column(db.Text, comment='任务说明')
    tagging_features = db.Column(db.Text, comment='打标特征JSON，存储特征ID列表')
    filter_keywords = db.Column(db.Text, comment='筛选条件关键字JSON，关键字列表')
    total_count = db.Column(db.Integer, nullable=False, default=0, comment='总图片数')
    processed_count = db.Column(db.Integer, nullable=False, default=0, comment='已处理图片数')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending, running, paused, completed, failed')
    note = db.Column(db.Text, comment='备注')
    last_error = db.Column(db.Text, comment='最后错误信息')
    started_at = db.Column(db.DateTime, comment='开始时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'tagging_features': json.loads(self.tagging_features) if self.tagging_features else [],
            'filter_keywords': json.loads(self.filter_keywords) if self.filter_keywords else [],
            'total_count': self.total_count,
            'processed_count': self.processed_count,
            'progress': round((self.processed_count / self.total_count * 100), 2) if self.total_count > 0 else 0,
            'status': self.status,
            'note': self.note or '',
            'last_error': self.last_error or '',
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

