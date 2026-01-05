# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class ImageTaggingResultHistory(db.Model):
    """图片打标结果历史模型"""
    __tablename__ = 'image_tagging_results_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tagging_task_id = db.Column(db.Integer, db.ForeignKey('tagging_tasks.id', ondelete='CASCADE'), nullable=False, comment='打标任务ID')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'), nullable=False, comment='图片ID')
    feature_id = db.Column(db.Integer, db.ForeignKey('features.id', ondelete='CASCADE'), nullable=False, comment='特征ID')
    tagging_value = db.Column(db.String(500), comment='打标值')
    source_task_id = db.Column(db.Integer, db.ForeignKey('tagging_tasks.id', ondelete='SET NULL'), comment='来源任务ID（如果复用其他任务的结果，记录原始任务ID）')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        {'comment': '图片打标结果历史表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'tagging_task_id': self.tagging_task_id,
            'image_id': self.image_id,
            'feature_id': self.feature_id,
            'tagging_value': self.tagging_value,
            'source_task_id': self.source_task_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

