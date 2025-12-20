from app.database import db
from datetime import datetime

class Feature(db.Model):
    """特征模型"""
    __tablename__ = 'features'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='特征名称')
    description = db.Column(db.String(255), comment='特征描述')
    category = db.Column(db.String(100), comment='特征分类')
    color = db.Column(db.String(30), comment='显示颜色')
    auto_tagging = db.Column(db.Boolean, nullable=False, default=False, comment='自动标注')
    values_json = db.Column(db.Text, comment='特征值JSON')
    enabled = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'color': self.color,
            'auto_tagging': self.auto_tagging,
            'values_json': self.values_json,
            'enabled': self.enabled,
            'status': 'active' if self.enabled else 'inactive',  # 兼容前端
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

