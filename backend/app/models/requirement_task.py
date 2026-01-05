# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class RequirementTask(db.Model):
    """需求任务关联模型"""
    __tablename__ = 'requirement_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False, comment='需求ID')
    task_type = db.Column(db.String(50), nullable=False, comment='任务类型：crawler(抓取), cleaning(清洗), tagging(打标), sample_set(样本集)')
    task_id = db.Column(db.Integer, nullable=False, comment='任务ID')
    task_order = db.Column(db.Integer, nullable=False, comment='任务顺序（1,2,3...）')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending(待执行), running(执行中), completed(已完成), failed(失败)')
    started_at = db.Column(db.DateTime, comment='开始时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    __table_args__ = (
        {'comment': '需求任务关联表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'task_type': self.task_type,
            'task_id': self.task_id,
            'task_order': self.task_order,
            'status': self.status,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

