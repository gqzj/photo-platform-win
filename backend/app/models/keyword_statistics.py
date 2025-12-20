# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class KeywordStatistics(db.Model):
    """关键字统计模型"""
    __tablename__ = 'keyword_statistics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    keyword = db.Column(db.String(500), nullable=False, unique=True, comment='关键字名称')
    image_count = db.Column(db.Integer, nullable=False, default=0, comment='图片总数')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'image_count': self.image_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

