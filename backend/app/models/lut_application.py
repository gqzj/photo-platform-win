# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutApplication(db.Model):
    """LUT应用任务模型"""
    __tablename__ = 'lut_applications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sample_image_id = db.Column(db.Integer, db.ForeignKey('sample_images.id', ondelete='CASCADE'), nullable=False, comment='样本图片ID')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending, running, completed, failed')
    total_lut_count = db.Column(db.Integer, default=0, comment='总LUT数量')
    processed_lut_count = db.Column(db.Integer, default=0, comment='已处理LUT数量')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    
    # 关联关系
    sample_image = db.relationship('SampleImage', backref='lut_applications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sample_image_id': self.sample_image_id,
            'status': self.status,
            'total_lut_count': self.total_lut_count,
            'processed_lut_count': self.processed_lut_count,
            'error_message': self.error_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None
        }

class LutAppliedImage(db.Model):
    """LUT应用后的图片模型"""
    __tablename__ = 'lut_applied_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    lut_application_id = db.Column(db.Integer, db.ForeignKey('lut_applications.id', ondelete='CASCADE'), nullable=False, comment='LUT应用任务ID')
    lut_file_id = db.Column(db.Integer, db.ForeignKey('lut_files.id', ondelete='CASCADE'), nullable=False, comment='LUT文件ID')
    sample_image_id = db.Column(db.Integer, db.ForeignKey('sample_images.id', ondelete='CASCADE'), nullable=False, comment='样本图片ID')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    storage_path = db.Column(db.String(500), nullable=False, comment='存储路径')
    file_size = db.Column(db.BigInteger, comment='文件大小（字节）')
    width = db.Column(db.Integer, comment='图片宽度')
    height = db.Column(db.Integer, comment='图片高度')
    format = db.Column(db.String(20), comment='图片格式')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    # 关联关系
    lut_application = db.relationship('LutApplication', backref='applied_images')
    lut_file = db.relationship('LutFile', backref='applied_images')
    sample_image = db.relationship('SampleImage', backref='applied_images')
    
    def to_dict(self):
        return {
            'id': self.id,
            'lut_application_id': self.lut_application_id,
            'lut_file_id': self.lut_file_id,
            'lut_file_name': self.lut_file.original_filename if self.lut_file else None,
            'sample_image_id': self.sample_image_id,
            'filename': self.filename,
            'storage_path': self.storage_path,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

