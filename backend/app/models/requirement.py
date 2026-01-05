from app.database import db
from datetime import datetime
import json

class Requirement(db.Model):
    """需求管理模型"""
    __tablename__ = 'requirements'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = db.Column(db.String(200), nullable=False, comment='需求名称')
    requester = db.Column(db.String(100), comment='需求发起人')
    keywords_json = db.Column(db.Text, comment='抓取的关键字范围JSON')
    cookie_id = db.Column(db.Integer, nullable=True, comment='抓取任务使用的账号ID（Cookie ID）')
    cleaning_features_json = db.Column(db.Text, comment='清洗任务的筛选特征JSON')
    tagging_features_json = db.Column(db.Text, comment='需要打标的特征JSON')
    sample_set_features_json = db.Column(db.Text, comment='样本集的特征范围JSON')
    status = db.Column(db.String(50), nullable=False, default='pending', comment='状态：pending(待处理), active(进行中), completed(已完成), cancelled(已取消)')
    progress_json = db.Column(db.Text, comment='进度JSON，记录各任务节点的状态和进度')
    note = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        def parse_json_field(field_value):
            """解析JSON字段"""
            if not field_value:
                return None
            try:
                return json.loads(field_value) if isinstance(field_value, str) else field_value
            except:
                return None
        
        return {
            'id': self.id,
            'name': self.name,
            'requester': self.requester or '',
            'keywords_json': self.keywords_json,
            'keywords': parse_json_field(self.keywords_json),
            'cookie_id': self.cookie_id,
            'cleaning_features_json': self.cleaning_features_json,
            'cleaning_features': parse_json_field(self.cleaning_features_json),
            'tagging_features_json': self.tagging_features_json,
            'tagging_features': parse_json_field(self.tagging_features_json),
            'sample_set_features_json': self.sample_set_features_json,
            'sample_set_features': parse_json_field(self.sample_set_features_json),
            'status': self.status,
            'progress_json': self.progress_json,
            'progress': parse_json_field(self.progress_json),
            'note': self.note or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

