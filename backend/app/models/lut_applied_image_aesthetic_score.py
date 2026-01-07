# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime
import json

class LutAppliedImageAestheticScore(db.Model):
    """LUT应用后图片的美学评分模型"""
    __tablename__ = 'lut_applied_image_aesthetic_scores'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    lut_applied_image_id = db.Column(db.Integer, db.ForeignKey('lut_applied_images.id', ondelete='CASCADE'), nullable=False, comment='LUT应用后图片ID')
    evaluator_type = db.Column(db.String(50), nullable=False, comment='评分器类型：artimuse, q_insight')
    score = db.Column(db.Numeric(10, 4), comment='美学评分分数')
    details_json = db.Column(db.Text, comment='接口返回的详细信息JSON')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    lut_applied_image = db.relationship('LutAppliedImage', backref='aesthetic_scores')
    
    __table_args__ = (
        db.UniqueConstraint('lut_applied_image_id', 'evaluator_type', name='uk_lut_applied_image_evaluator'),
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
            'lut_applied_image_id': self.lut_applied_image_id,
            'evaluator_type': self.evaluator_type,
            'score': float(self.score) if self.score is not None else None,
            'details': details_data,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

