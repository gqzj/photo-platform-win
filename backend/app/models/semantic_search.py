# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class SemanticSearchImage(db.Model):
    """语义搜索图片模型 - 记录已编码到向量数据库的图片"""
    __tablename__ = 'semantic_search_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'), nullable=False, unique=True, comment='图片ID')
    vector_id = db.Column(db.String(100), nullable=True, comment='FAISS索引位置（已废弃，保留用于兼容）')
    encoded = db.Column(db.Boolean, nullable=False, default=False, comment='是否已编码')
    encoded_at = db.Column(db.DateTime, nullable=True, comment='编码时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    image = db.relationship('Image', backref='semantic_search')
    
    __table_args__ = (
        db.Index('idx_image_id', 'image_id'),
        db.Index('idx_encoded', 'encoded'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'vector_id': self.vector_id,
            'encoded': self.encoded,
            'encoded_at': self.encoded_at.strftime('%Y-%m-%d %H:%M:%S') if self.encoded_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
