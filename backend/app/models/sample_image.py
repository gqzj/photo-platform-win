# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class SampleImage(db.Model):
    """样本图片模型"""
    __tablename__ = 'sample_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    original_filename = db.Column(db.String(255), nullable=False, comment='原始文件名')
    storage_path = db.Column(db.String(500), nullable=False, comment='存储路径')
    file_size = db.Column(db.BigInteger, comment='文件大小（字节）')
    file_hash = db.Column(db.String(128), comment='文件哈希值')
    width = db.Column(db.Integer, comment='图片宽度')
    height = db.Column(db.Integer, comment='图片高度')
    format = db.Column(db.String(20), comment='图片格式')
    description = db.Column(db.Text, comment='图片描述')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'storage_path': self.storage_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

