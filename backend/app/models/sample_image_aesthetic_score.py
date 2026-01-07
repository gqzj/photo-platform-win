# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime
import json

class SampleImageAestheticScore(db.Model):
    """样本图片美学评分模型"""
    __tablename__ = 'sample_image_aesthetic_scores'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sample_image_id = db.Column(db.Integer, db.ForeignKey('sample_images.id', ondelete='CASCADE'), nullable=False, comment='样本图片ID')
    evaluator_type = db.Column(db.String(50), nullable=False, comment='评分器类型：artimuse, q_insight')
    score = db.Column(db.Numeric(10, 4), comment='美学评分分数')
    details_json = db.Column(db.Text, comment='接口返回的详细信息JSON')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    sample_image = db.relationship('SampleImage', backref='aesthetic_scores')
    
    __table_args__ = (
        db.UniqueConstraint('sample_image_id', 'evaluator_type', name='uk_sample_image_evaluator'),
    )
    
    def to_dict(self):
        """转换为字典"""
        details_data = None
        if self.details_json:
            try:
                details_data = json.loads(self.details_json) if isinstance(self.details_json, str) else self.details_json
            except:
                details_data = None
        
        return {
            'id': self.id,
            'sample_image_id': self.sample_image_id,
            'evaluator_type': self.evaluator_type,
            'score': float(self.score) if self.score is not None else None,
            'details': details_data,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class SampleImageAestheticScoreTask(db.Model):
    """样本图片美学评分任务模型"""
    __tablename__ = 'sample_image_aesthetic_score_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending, running, completed, failed')
    evaluator_type = db.Column(db.String(50), nullable=False, comment='评分器类型：artimuse, q_insight')
    score_mode = db.Column(db.String(50), nullable=False, default='score_and_reason', comment='评分模式：score_only, score_and_reason')
    total_image_count = db.Column(db.Integer, default=0, comment='总图片数量')
    processed_image_count = db.Column(db.Integer, default=0, comment='已处理图片数量')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    
    def to_dict(self):
        return {
            'id': self.id,
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

