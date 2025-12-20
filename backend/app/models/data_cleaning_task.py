from app.database import db
from datetime import datetime

class DataCleaningTask(db.Model):
    """数据清洗任务模型"""
    __tablename__ = 'data_cleaning_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, comment='任务名称')
    filter_features = db.Column(db.Text, comment='筛选特征JSON，例如：["无人脸", "多人脸", "包含文字", "图片模糊"]')
    filter_keywords = db.Column(db.Text, comment='筛选范围关键字JSON，关键字列表')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending, running, paused, completed, failed')
    processed_count = db.Column(db.Integer, nullable=False, default=0, comment='任务处理总数')
    note = db.Column(db.Text, comment='备注')
    last_error = db.Column(db.Text, comment='最后错误信息')
    started_at = db.Column(db.DateTime, comment='开始时间')
    finished_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'filter_features': json.loads(self.filter_features) if self.filter_features else [],
            'filter_keywords': json.loads(self.filter_keywords) if self.filter_keywords else [],
            'status': self.status,
            'processed_count': self.processed_count,
            'note': self.note or '',
            'last_error': self.last_error or '',
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

