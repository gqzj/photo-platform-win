# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutFileTag(db.Model):
    """LUT文件标签模型"""
    __tablename__ = 'lut_file_tags'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    lut_file_id = db.Column(db.Integer, db.ForeignKey('lut_files.id', ondelete='CASCADE'), nullable=False, comment='LUT文件ID')
    tone = db.Column(db.String(50), comment='色调：暖调、冷调、中性调')
    saturation = db.Column(db.String(50), comment='饱和度：高饱和、中饱和、低饱和')
    contrast = db.Column(db.String(50), comment='对比度：高对比、中对比、低对比')
    h_mean = db.Column(db.Numeric(10, 4), comment='色调均值')
    s_mean = db.Column(db.Numeric(10, 4), comment='饱和度均值')
    s_var = db.Column(db.Numeric(10, 4), comment='饱和度方差')
    v_var = db.Column(db.Numeric(10, 4), comment='明度方差')
    contrast_rgb = db.Column(db.Numeric(10, 4), comment='RGB对比度')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    lut_file = db.relationship('LutFile', backref='tags')
    
    __table_args__ = (
        db.UniqueConstraint('lut_file_id', name='uk_lut_file_tag'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'lut_file_id': self.lut_file_id,
            'tone': self.tone,
            'saturation': self.saturation,
            'contrast': self.contrast,
            'h_mean': float(self.h_mean) if self.h_mean is not None else None,
            's_mean': float(self.s_mean) if self.s_mean is not None else None,
            's_var': float(self.s_var) if self.s_var is not None else None,
            'v_var': float(self.v_var) if self.v_var is not None else None,
            'contrast_rgb': float(self.contrast_rgb) if self.contrast_rgb is not None else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

