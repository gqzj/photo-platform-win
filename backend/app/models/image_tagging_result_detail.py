# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class ImageTaggingResultDetail(db.Model):
    """图片打标结果明细模型"""
    __tablename__ = 'image_tagging_results_detail'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'), nullable=False, comment='图片ID')
    feature_id = db.Column(db.Integer, db.ForeignKey('features.id', ondelete='CASCADE'), nullable=False, comment='特征ID')
    tagging_value = db.Column(db.String(500), comment='打标值')
    last_tagging_task_id = db.Column(db.Integer, db.ForeignKey('tagging_tasks.id', ondelete='SET NULL'), comment='最后打标任务ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 唯一约束：同一图片、同一特征只能有一条记录
    __table_args__ = (
        db.UniqueConstraint('image_id', 'feature_id', name='uk_image_feature'),
        {'comment': '图片打标结果明细表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'image_id': self.image_id,
            'feature_id': self.feature_id,
            'tagging_value': self.tagging_value,
            'last_tagging_task_id': self.last_tagging_task_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

