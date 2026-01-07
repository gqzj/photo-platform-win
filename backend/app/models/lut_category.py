# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutCategory(db.Model):
    """Lut分类模型"""
    __tablename__ = 'lut_categories'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    description = db.Column(db.Text, comment='分类描述')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

