# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutAppliedImagePreference(db.Model):
    """LUT应用结果图片的用户偏好模型"""
    __tablename__ = 'lut_applied_image_preferences'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    lut_applied_image_id = db.Column(db.Integer, db.ForeignKey('lut_applied_images.id', ondelete='CASCADE'), nullable=False, comment='LUT应用结果图片ID')
    is_liked = db.Column(db.Boolean, nullable=False, comment='是否喜欢：True=喜欢, False=不喜欢')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    lut_applied_image = db.relationship('LutAppliedImage', backref='preferences')
    
    __table_args__ = (
        db.UniqueConstraint('lut_applied_image_id', name='uk_lut_applied_image_preference'),
        db.Index('idx_lut_applied_image_id', 'lut_applied_image_id'),
        db.Index('idx_is_liked', 'is_liked'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'lut_applied_image_id': self.lut_applied_image_id,
            'is_liked': self.is_liked,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
