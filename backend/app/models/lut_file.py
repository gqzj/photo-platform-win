# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutFile(db.Model):
    """Lut文件模型"""
    __tablename__ = 'lut_files'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    category_id = db.Column(db.Integer, db.ForeignKey('lut_categories.id', ondelete='SET NULL'), nullable=True, comment='分类ID')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    original_filename = db.Column(db.String(255), nullable=False, comment='原始文件名')
    storage_path = db.Column(db.String(500), nullable=False, comment='存储路径')
    file_size = db.Column(db.BigInteger, comment='文件大小（字节）')
    file_hash = db.Column(db.String(128), comment='文件哈希值')
    thumbnail_path = db.Column(db.String(500), comment='缩略图路径')
    description = db.Column(db.Text, comment='文件描述')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    category = db.relationship('LutCategory', backref='lut_files')
    
    __table_args__ = (
        db.UniqueConstraint('category_id', 'original_filename', name='uk_category_original_filename'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'storage_path': self.storage_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'thumbnail_path': self.thumbnail_path,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

