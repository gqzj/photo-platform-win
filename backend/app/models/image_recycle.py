# -*- coding: utf-8 -*-
"""图片回收站模型"""
from app.database import db
from datetime import datetime
import json

class ImageRecycle(db.Model):
    """图片回收站模型"""
    __tablename__ = 'images_recycle'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    original_image_id = db.Column(db.Integer, comment='原图片ID')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    storage_path = db.Column(db.String(500), nullable=False, comment='存储路径')
    original_url = db.Column(db.String(1000), comment='原始URL')
    status = db.Column(db.String(50), nullable=False, default='recycled', comment='状态')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    storage_mode = db.Column(db.String(20), nullable=False, default='local', comment='存储模式')
    source_site = db.Column(db.String(100), comment='来源网站')
    keyword = db.Column(db.String(500), comment='关键词')
    hash_tags_json = db.Column(db.Text, comment='标签JSON')
    visit_url = db.Column(db.String(2000), comment='访问URL')
    image_hash = db.Column(db.String(128), comment='图片哈希值')
    width = db.Column(db.Integer, comment='图片宽度')
    height = db.Column(db.Integer, comment='图片高度')
    format = db.Column(db.String(20), comment='图片格式')
    cleaning_task_id = db.Column(db.Integer, comment='清洗任务ID')
    cleaning_reason = db.Column(db.String(500), comment='清洗原因')
    recycled_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='回收时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_image_id': self.original_image_id,
            'filename': self.filename,
            'storage_path': self.storage_path,
            'original_url': self.original_url,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'storage_mode': self.storage_mode,
            'source_site': self.source_site,
            'keyword': self.keyword,
            'hash_tags_json': self.hash_tags_json,
            'visit_url': self.visit_url,
            'image_hash': self.image_hash,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'cleaning_task_id': self.cleaning_task_id,
            'cleaning_reason': self.cleaning_reason,
            'recycled_at': self.recycled_at.strftime('%Y-%m-%d %H:%M:%S') if self.recycled_at else None
        }

