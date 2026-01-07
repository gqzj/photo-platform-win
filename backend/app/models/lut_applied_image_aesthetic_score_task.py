# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutAppliedImageAestheticScoreTask(db.Model):
    """LUT应用后图片美学评分任务模型"""
    __tablename__ = 'lut_applied_image_aesthetic_score_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sample_image_id = db.Column(db.Integer, db.ForeignKey('sample_images.id', ondelete='CASCADE'), nullable=False, comment='样本图片ID')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending, running, completed, failed')
    evaluator_type = db.Column(db.String(50), nullable=False, comment='评分器类型：artimuse, q_insight')
    score_mode = db.Column(db.String(50), nullable=False, default='score_and_reason', comment='评分模式：score_only, score_and_reason')
    total_image_count = db.Column(db.Integer, default=0, comment='总图片数量')
    processed_image_count = db.Column(db.Integer, default=0, comment='已处理图片数量')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    
    # 关联关系
    sample_image = db.relationship('SampleImage', backref='lut_applied_image_aesthetic_score_tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sample_image_id': self.sample_image_id,
            'status': self.status,
            'evaluator_type': self.evaluator_type,
            'score_mode': self.score_mode,
            'total_image_count': self.total_image_count,
            'processed_image_count': self.processed_image_count,
            'error_message': self.error_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None
        }

