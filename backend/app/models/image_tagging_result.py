# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class ImageTaggingResult(db.Model):
    """图片打标结果模型"""
    __tablename__ = 'image_tagging_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tagging_task_id = db.Column(db.Integer, db.ForeignKey('tagging_tasks.id', ondelete='CASCADE'), nullable=False, comment='打标任务ID')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'), nullable=False, comment='图片ID')
    feature_id = db.Column(db.Integer, db.ForeignKey('features.id', ondelete='CASCADE'), nullable=False, comment='特征ID')
    tagging_value = db.Column(db.String(500), comment='打标值（单个特征的值）')
    tagging_result_json = db.Column(db.Text, comment='完整的打标结果JSON（包含所有特征）')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 唯一约束：同一任务、同一图片、同一特征只能有一条记录
    __table_args__ = (
        db.UniqueConstraint('tagging_task_id', 'image_id', 'feature_id', name='uk_task_image_feature'),
        {'comment': '图片打标结果表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        result_json = None
        if self.tagging_result_json:
            try:
                result_json = json.loads(self.tagging_result_json) if isinstance(self.tagging_result_json, str) else self.tagging_result_json
            except:
                result_json = self.tagging_result_json
        
        return {
            'id': self.id,
            'tagging_task_id': self.tagging_task_id,
            'image_id': self.image_id,
            'feature_id': self.feature_id,
            'tagging_value': self.tagging_value,
            'tagging_result_json': result_json,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

