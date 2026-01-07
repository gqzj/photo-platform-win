# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutFileAnalysisTask(db.Model):
    """LUT文件分析任务模型"""
    __tablename__ = 'lut_file_analysis_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending, running, completed, failed')
    total_file_count = db.Column(db.Integer, default=0, comment='总文件数量')
    processed_file_count = db.Column(db.Integer, default=0, comment='已处理文件数量')
    success_count = db.Column(db.Integer, default=0, comment='成功数量')
    failed_count = db.Column(db.Integer, default=0, comment='失败数量')
    interrupted = db.Column(db.Boolean, default=False, nullable=False, comment='是否被中断：0-否，1-是')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'total_file_count': self.total_file_count,
            'processed_file_count': self.processed_file_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'interrupted': self.interrupted,
            'error_message': self.error_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None
        }

